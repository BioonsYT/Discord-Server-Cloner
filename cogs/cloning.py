# cogs/cloning.py
import discord
from discord import app_commands
from discord.ext import commands
import json
import asyncio
import datetime

# --- ATENÇÃO ---
# V29.3 - Adicionado filtro no Onboarding para previnir erro de 'Invalid Form Body'.

class CloningV29_3(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.template_file = "template.json"
        self.maps_file = "clone_maps.json"

    def _save_template(self, data):
        with open(self.template_file, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)
    def _load_template(self):
        try:
            with open(self.template_file, 'r', encoding='utf-8') as f:
                content = f.read(); return json.loads(content) if content else None
        except (FileNotFoundError, json.JSONDecodeError): return None
    def _save_maps(self, data):
        with open(self.maps_file, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
    def _load_maps(self):
        try:
            with open(self.maps_file, 'r', encoding='utf-8') as f:
                content = f.read(); return json.loads(content) if content else {}
        except (FileNotFoundError, json.JSONDecodeError): return {}
    def _remap_onboarding_ids(self, obj, role_id_map, channel_id_map):
        if isinstance(obj, dict):
            new_dict = {}
            for k, v in obj.items():
                if k in ('role_ids', 'additional_role_ids') and isinstance(v, list):
                    new_ids = [role_id_map.get(str(rid)) for rid in v if str(rid) in role_id_map]
                    new_dict[k] = [i for i in new_ids if i is not None]
                elif k in ('channel_ids', 'default_channel_ids') and isinstance(v, list):
                    new_ids = [channel_id_map.get(str(cid)) for cid in v if str(cid) in channel_id_map]
                    new_dict[k] = [i for i in new_ids if i is not None]
                else: new_dict[k] = self._remap_onboarding_ids(v, role_id_map, channel_id_map)
            return new_dict
        elif isinstance(obj, list): return [self._remap_onboarding_ids(item, role_id_map, channel_id_map) for item in obj]
        else: return obj

    @app_commands.command(name="clonar", description="Salva a estrutura completa do servidor.")
    @app_commands.checks.has_permissions(administrator=True)
    async def clonar(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild
        template = {"guild_settings": {}, "bots": [], "roles": [], "categories": [], "onboarding": {}, "booster_role_overwrites": {}}
        
        template["guild_settings"] = {
            "name": guild.name,
            "system_channel_id": guild.system_channel.id if guild.system_channel else None,
            "rules_channel_id": guild.rules_channel.id if guild.rules_channel else None,
            "public_updates_channel_id": guild.public_updates_channel.id if guild.public_updates_channel else None,
            "afk_channel_id": guild.afk_channel.id if guild.afk_channel else None,
            "afk_timeout": guild.afk_timeout
        }
        
        if booster_role := guild.premium_subscriber_role:
            booster_overwrites = {}
            for channel in guild.channels:
                if overwrite := channel.overwrites_for(booster_role):
                    if not overwrite.is_empty():
                        booster_overwrites[str(channel.id)] = {"allow": overwrite.pair()[0].value, "deny": overwrite.pair()[1].value}
            template["booster_role_overwrites"] = booster_overwrites
        for member in guild.members:
            if member.bot:
                if managed_role := next((r for r in member.roles if r.managed and r.tags and r.tags.bot_id == member.id), None):
                    overwrites_data = {}
                    for channel in guild.channels:
                        if overwrite := channel.overwrites_for(managed_role):
                            if not overwrite.is_empty(): overwrites_data[str(channel.id)] = {"allow": overwrite.pair()[0].value, "deny": overwrite.pair()[1].value}
                    template["bots"].append({"id": member.id, "name": member.name, "managed_role": {"permissions": managed_role.permissions.value, "position": managed_role.position, "overwrites": overwrites_data}, "extra_roles_ids": [r.id for r in member.roles if not r.managed and not r.is_default()]})
        roles_data = [r for r in sorted(guild.roles, key=lambda r: r.position, reverse=True) if not r.is_default() and not r.managed and not r.is_premium_subscriber()]
        for role in roles_data: template["roles"].append({"id": role.id, "name": role.name, "position": role.position, "permissions": role.permissions.value, "color": role.color.value, "hoist": role.hoist, "mentionable": role.mentionable})
        for category in guild.categories:
            channels_in_cat = []
            for channel in sorted(category.channels, key=lambda c: c.position):
                topic = channel.topic if channel.type in (discord.ChannelType.text, discord.ChannelType.forum, discord.ChannelType.news) else None
                channel_data = {"id": channel.id, "name": channel.name, "type": str(channel.type), "topic": topic, "overwrites": {r.name: {"allow": o.pair()[0].value, "deny": o.pair()[1].value} for r, o in channel.overwrites.items() if isinstance(r, discord.Role) and not r.is_premium_subscriber()}}
                if channel.type == discord.ChannelType.forum: channel_data["tags"] = [{"name": tag.name, "emoji": str(tag.emoji) if tag.emoji else None, "moderated": tag.moderated} for tag in channel.available_tags]
                channels_in_cat.append(channel_data)
            template["categories"].append({"id": category.id, "name": category.name, "channels": channels_in_cat, "overwrites": {r.name: {"allow": o.pair()[0].value, "deny": o.pair()[1].value} for r, o in category.overwrites.items() if isinstance(r, discord.Role) and not r.is_premium_subscriber()}})
        try:
            template["onboarding"] = await self.bot.http.get_guild_onboarding(guild.id)
        except Exception as e: print(f"Não foi possível clonar o Onboarding: {e}")
        self._save_template(template)
        await interaction.followup.send(f"✅ Estrutura final e configurações salvas com sucesso!", ephemeral=True)

    @app_commands.command(name="colar_estrutura", description="PASSO 1: Cria cargos e canais (exceto fóruns).")
    @app_commands.checks.has_permissions(administrator=True)
    async def colar_estrutura(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        template = self._load_template(); guild = interaction.guild
        if not template: await interaction.followup.send("❌ Template não encontrado!", ephemeral=True); return
        print("\n--- INICIANDO ETAPA DE LIMPEZA ---"); await interaction.followup.send("⚠️ Limpando servidor...", ephemeral=True)
        for item in await guild.fetch_automod_rules():
            try: await item.delete()
            except: pass
        for item in guild.channels:
            try: await item.delete()
            except: pass
        for item in guild.roles:
            if not item.is_default() and not item.managed and not item.is_premium_subscriber():
                try: await item.delete()
                except: pass
        self._save_maps({})
        print("--- LIMP. CONCLUÍDA ---")
        print("\n--- INICIANDO ETAPA DE CARGOS ---"); await interaction.edit_original_response(content="Criando cargos...")
        role_id_map, role_name_map, created_roles = {}, {}, []
        for role_data in template["roles"]:
            new_role = await guild.create_role(name=role_data["name"], permissions=discord.Permissions(role_data["permissions"]), color=discord.Color(role_data["color"]), hoist=role_data["hoist"], mentionable=role_data["mentionable"])
            role_id_map[str(role_data["id"])], role_name_map[role_data["name"]] = new_role.id, new_role
            created_roles.append(new_role)
            await asyncio.sleep(1)
        positions = {role: pos for pos, role in enumerate(reversed(created_roles), 1)}
        try: await guild.edit_role_positions(positions=positions)
        except discord.HTTPException as e: print(f"AVISO: Não foi possível reordenar os cargos: {e}")
        maps = self._load_maps(); maps["roles"] = role_id_map; self._save_maps(maps)
        print("--- CARGOS CONCLUÍDOS ---")
        print("\n--- INICIANDO ETAPA DE CANAIS (Exceto Fóruns) ---"); await interaction.edit_original_response(content="Criando canais...")
        channel_id_map = maps.get("channels", {})
        for category_data in template["categories"]:
            overwrites = {role_name_map.get(r_name, guild.default_role): discord.PermissionOverwrite.from_pair(discord.Permissions(p["allow"]), discord.Permissions(p["deny"])) for r_name, p in category_data["overwrites"].items()}
            new_category = await guild.create_category(name=category_data["name"], overwrites=overwrites)
            channel_id_map[str(category_data["id"])] = new_category.id
            await asyncio.sleep(1)
            for channel_data in category_data["channels"]:
                if channel_data["type"] == 'forum': continue
                chan_overwrites = {role_name_map.get(r_name, guild.default_role): discord.PermissionOverwrite.from_pair(discord.Permissions(p["allow"]), discord.Permissions(p["deny"])) for r_name, p in channel_data["overwrites"].items()}
                new_channel = None
                if (channel_type := channel_data["type"]) == 'text' or channel_type == 'news':
                    new_channel = await guild.create_text_channel(name=channel_data["name"], topic=channel_data.get("topic"), overwrites=chan_overwrites, category=new_category)
                    if channel_type == 'news' and isinstance(new_channel, discord.TextChannel):
                        try: await new_channel.edit(news=True)
                        except Exception as e: print(f"AVISO: Não promover '{new_channel.name}' p/ Anúncios: {e}")
                elif channel_type == 'voice': new_channel = await guild.create_voice_channel(name=channel_data["name"], overwrites=chan_overwrites, category=new_category)
                if new_channel: channel_id_map[str(channel_data["id"])] = new_channel.id
                await asyncio.sleep(1)
        maps["channels"] = channel_id_map; self._save_maps(maps)
        print("--- CANAIS CONCLUÍDOS ---\n")
        await interaction.edit_original_response(content="✅ **ESTRUTURA CONCLUÍDA!**\n**Próximos passos:** `/colar_foruns`, `/colar_configuracoes`, `/colar_onboarding`, `/colar_booster` e depois convide os bots.")

    @app_commands.command(name="colar_foruns", description="PASSO 2: Cria todos os canais de fórum.")
    @app_commands.checks.has_permissions(administrator=True)
    async def colar_foruns(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild
        template, maps = self._load_template(), self._load_maps()
        if not template or "roles" not in maps: await interaction.followup.send("❌ Template ou mapa de cargos não encontrado!", ephemeral=True); return
        print("\n--- INICIANDO ETAPA DE FÓRUNS ---")
        role_name_map = {r.name: r for r in guild.roles}
        channel_id_map = maps.get("channels", {})
        for category_data in template["categories"]:
            if not (new_category := discord.utils.get(guild.categories, name=category_data["name"])): continue
            for channel_data in category_data["channels"]:
                if channel_data["type"] != 'forum': continue
                try:
                    chan_overwrites = {role_name_map.get(r_name, guild.default_role): discord.PermissionOverwrite.from_pair(discord.Permissions(p["allow"]), discord.Permissions(p["deny"])) for r_name, p in channel_data["overwrites"].items()}
                    tags = []
                    for tag_data in channel_data.get("tags", []):
                        emoji_str = tag_data.get("emoji")
                        valid_emoji = emoji_str if emoji_str and not emoji_str.startswith('<') and emoji_str != 'None' else None
                        try:
                            tags.append(discord.ForumTag(name=tag_data["name"], emoji=valid_emoji, moderated=tag_data.get("moderated", False)))
                        except:
                            try: tags.append(discord.ForumTag(name=tag_data["name"], moderated=tag_data.get("moderated", False)))
                            except Exception as e: print(f"!!!! ERRO: Falha ao criar a tag '{tag_data['name']}': {e}")
                    new_channel = await guild.create_forum(name=channel_data["name"], topic=channel_data.get("topic"), available_tags=tags, category=new_category, overwrites=chan_overwrites)
                    if new_channel: channel_id_map[str(channel_data["id"])] = new_channel.id
                    await asyncio.sleep(1)
                except Exception as e: print(f"!!!! ERRO ao criar fórum '{channel_data['name']}': {e}")
        maps["channels"] = channel_id_map; self._save_maps(maps)
        print("--- ETAPA DE FÓRUNS CONCLUÍDA ---\n")
        await interaction.followup.send("✅ Fóruns criados! Próximo passo: `/colar_configuracoes`.", ephemeral=True)

    @app_commands.command(name="colar_configuracoes", description="PASSO 3: Aplica as configurações gerais do servidor (nome, canais padrão, etc).")
    @app_commands.checks.has_permissions(administrator=True)
    async def colar_configuracoes(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild, template, maps = interaction.guild, self._load_template(), self._load_maps()
        if not (saved_settings := template.get("guild_settings")) or not maps: await interaction.followup.send("❌ Template ou mapa de IDs não encontrado.", ephemeral=True); return
        print("\n--- INICIANDO ETAPA DE CONFIGURAÇÕES GERAIS ---")
        channel_id_map = maps.get("channels", {})
        
        settings_to_apply = {}
        if old_sys_chan_id := saved_settings.get("system_channel_id"):
            if new_chan_id := channel_id_map.get(str(old_sys_chan_id)):
                if new_chan_obj := guild.get_channel(new_chan_id): settings_to_apply["system_channel"] = new_chan_obj
        if old_rules_chan_id := saved_settings.get("rules_channel_id"):
            if new_chan_id := channel_id_map.get(str(old_rules_chan_id)):
                if new_chan_obj := guild.get_channel(new_chan_id): settings_to_apply["rules_channel"] = new_chan_obj
        if old_updates_chan_id := saved_settings.get("public_updates_channel_id"):
            if new_chan_id := channel_id_map.get(str(old_updates_chan_id)):
                if new_chan_obj := guild.get_channel(new_chan_id): settings_to_apply["public_updates_channel"] = new_chan_obj
        if old_afk_chan_id := saved_settings.get("afk_channel_id"):
            if new_chan_id := channel_id_map.get(str(old_afk_chan_id)):
                if new_chan_obj := guild.get_channel(new_chan_id): settings_to_apply["afk_channel"] = new_chan_obj

        settings_to_apply["afk_timeout"] = saved_settings.get("afk_timeout")
        settings_to_apply["name"] = saved_settings.get("name")
        
        try:
            await guild.edit(**settings_to_apply, reason="Clonagem Final")
            print("--- ETAPA DE CONFIGURAÇÕES GERAIS CONCLUÍDA ---\n")
            await interaction.followup.send("✅ **Configurações gerais do servidor aplicadas com sucesso!**", ephemeral=True)
        except Exception as e:
            print(f"!!!! FALHA ao aplicar configurações gerais: {e}")
            await interaction.followup.send(f"❌ **Falha ao aplicar as configurações.** Verifique o console.", ephemeral=True)


    @app_commands.command(name="colar_onboarding", description="PASSO 4: Aplica as configurações de Onboarding.")
    @app_commands.checks.has_permissions(administrator=True)
    async def colar_onboarding(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild, template, maps = interaction.guild, self._load_template(), self._load_maps()
        if not (onboarding_payload := template.get("onboarding")) or not maps: await interaction.followup.send("❌ Template ou mapa de IDs não encontrado.", ephemeral=True); return
        print("\n--- INICIANDO ETAPA DE ONBOARDING ---")
        role_id_map, channel_id_map = maps.get("roles", {}), maps.get("channels", {})
        try:
            remapped_payload = self._remap_onboarding_ids(onboarding_payload, role_id_map, channel_id_map)

            # --- NOVO FILTRO DE SEGURANÇA ---
            if 'prompts' in remapped_payload:
                for prompt in remapped_payload['prompts']:
                    if 'options' in prompt:
                        valid_options = []
                        for option in prompt['options']:
                            has_roles = 'role_ids' in option and option['role_ids']
                            has_channels = 'channel_ids' in option and option['channel_ids']
                            if has_roles or has_channels:
                                valid_options.append(option)
                        prompt['options'] = valid_options

            await self.bot.http.request(discord.http.Route('PUT', f'/guilds/{guild.id}/onboarding'), json=remapped_payload)
            print("--- ETAPA DE ONBOARDING CONCLUÍDA ---\n")
            await interaction.followup.send("✅ **Onboarding aplicado com sucesso!**", ephemeral=True)
        except Exception as e:
            print(f"!!!! FALHA CRÍTICA ao aplicar Onboarding: {e}")
            await interaction.followup.send(f"❌ **Falha ao aplicar Onboarding.** Verifique o console.", ephemeral=True)

    @app_commands.command(name="colar_booster", description="PASSO EXTRA: Sincroniza as permissões do cargo de Booster.")
    @app_commands.checks.has_permissions(administrator=True)
    async def colar_booster(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild
        template, maps = self._load_template(), self._load_maps()
        if not (target_booster_role := guild.premium_subscriber_role):
            await interaction.followup.send("❌ Este servidor não possui um cargo de Booster configurado.", ephemeral=True); return
        if not template or not maps or "booster_role_overwrites" not in template:
            await interaction.followup.send("❌ Template ou mapa de IDs não encontrado.", ephemeral=True); return
        print("\n--- INICIANDO ETAPA DE PERMISSÕES DE BOOSTER ---")
        channel_id_map = maps.get("channels", {})
        booster_overwrites = template.get("booster_role_overwrites", {})
        canais_atualizados, falhas = 0, 0
        for old_channel_id, perms_data in booster_overwrites.items():
            try:
                if new_channel_id := channel_id_map.get(str(old_channel_id)):
                    if channel := guild.get_channel(new_channel_id):
                        overwrite = discord.PermissionOverwrite.from_pair(discord.Permissions(perms_data["allow"]), discord.Permissions(perms_data["deny"]))
                        await channel.set_permissions(target_booster_role, overwrite=overwrite, reason="Clonagem Final")
                        print(f"--> Permissões do Booster aplicadas em: #{channel.name}")
                        canais_atualizados += 1; await asyncio.sleep(0.5)
            except Exception as e: print(f"!!!! ERRO ao aplicar perms de Booster: {e}"); falhas += 1
        print("--- ETAPA DE PERMISSÕES DE BOOSTER CONCLUÍDA ---\n")
        await interaction.followup.send(f"✅ **Permissões de Booster Sincronizadas!**\n- {canais_atualizados} canais atualizados.\n- {falhas} falhas.", ephemeral=True)

    @app_commands.command(name="configurar_bots", description="PASSO FINAL: Aplica as configurações nos bots.")
    @app_commands.checks.has_permissions(administrator=True)
    async def configurar_bots(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild, template, maps = interaction.guild, self._load_template(), self._load_maps()
        if not template or not maps or "bots" not in template: await interaction.followup.send("❌ Template ou mapa de IDs não encontrado.", ephemeral=True); return
        print("\n--- INICIANDO ETAPA DE CONFIGURAÇÃO DE BOTS ---")
        role_id_map, channel_id_map = maps.get("roles", {}), maps.get("channels", {})
        bots_configurados, bots_pulados = [], []
        for bot_data in template.get("bots", []):
            if not (bot_member := guild.get_member(bot_data["id"])): bots_pulados.append(bot_data['name']); continue
            try:
                print(f"--> Configurando bot: {bot_member.name}")
                if managed_role := next((r for r in bot_member.roles if r.managed and r.tags and r.tags.bot_id == bot_member.id), None):
                    print(f"---> Cargo gerenciado encontrado: {managed_role.name}. Aplicando permissões de servidor...")
                    await managed_role.edit(permissions=discord.Permissions(bot_data["managed_role"]["permissions"]), reason="Clonagem Final")
                    await asyncio.sleep(0.5)
                    
                    print(f"---> Aplicando permissões de canal...")
                    for old_chan_id, perms_data in bot_data["managed_role"]["overwrites"].items():
                        if (new_chan_id := channel_id_map.get(str(old_chan_id))) and (channel_to_edit := guild.get_channel(new_chan_id)):
                            overwrite = discord.PermissionOverwrite.from_pair(discord.Permissions(perms_data["allow"]), discord.Permissions(perms_data["deny"]))
                            await channel_to_edit.set_permissions(managed_role, overwrite=overwrite, reason="Clonagem Final")
                    
                    print(f"---> Verificando cargos extras...")
                    for extra_role_id in bot_data["extra_roles_ids"]:
                        if (new_role_id := role_id_map.get(str(extra_role_id))) and (new_role_obj := guild.get_role(new_role_id)):
                            await bot_member.add_roles(new_role_obj, reason="Clonagem Final")
                            print(f"----> Cargo extra '{new_role_obj.name}' adicionado.")
                    
                    try:
                        print(f"---> Movendo cargo para a posição correta...")
                        await managed_role.edit(position=bot_data["managed_role"]["position"], reason="Clonagem Final")
                    except discord.HTTPException:
                        print(f"----> AVISO: Não foi possível mover o cargo do bot '{bot_data['name']}'.")
                
                bots_configurados.append(bot_data["name"])
                await asyncio.sleep(1)
            except Exception as e: print(f"!!!! ERRO ao configurar o bot {bot_data['name']}: {e}"); bots_pulados.append(f"{bot_data['name']} (erro)")
        
        print("--- ETAPA DE CONFIGURAÇÃO DE BOTS CONCLUÍDA ---\n")
        relatorio = "✅ **PROCESSO DE CLONAGEM FINALIZADO!**\n\n"
        if bots_configurados: relatorio += f"**Bots Configurados:**\n- " + "\n- ".join(bots_configurados) + "\n\n"
        if bots_pulados: relatorio += f"**Bots Pulados:**\n- " + "\n- ".join(bots_pulados)
        await interaction.followup.send(relatorio, ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        send_method = interaction.followup.send if interaction.response.is_done() else interaction.response.send_message
        if isinstance(error, app_commands.MissingPermissions): await send_method("❌ Você precisa ser `Administrador` para usar este comando!", ephemeral=True)
        else:
            original_error = getattr(error, 'original', error)
            print(f"Ocorreu um erro não tratado: {original_error}")
            await send_method(f"Ocorreu um erro inesperado. Verifique o console do bot.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CloningV29_3(bot))