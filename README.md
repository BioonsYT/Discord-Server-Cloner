# Shadon Clone Bot - Clonador de Servidores Discord

<div align="center">

![Versão](https://img.shields.io/github/v/release/BioonsYT/Discord-Server-Cloner?style=for-the-badge)
![Linguagem](https://img.shields.io/github/languages/top/BioonsYT/Discord-Server-Cloner?style=for-the-badge)
![Licença](https://img.shields.io/github/license/BioonsYT/Discord-Server-Cloner?style=for-the-badge)

</div>

<p align="center">
  Uma ferramenta poderosa e completa para backup e clonagem de servidores do Discord, desenvolvida em Python com a biblioteca `discord.py`.
</p>

<div align="center">
  
![Demonstração dos Comandos do Shadon Clone](https://raw.githubusercontent.com/BioonsYT/Discord-Server-Cloner/main/cmds-shadon-clone.png)

</div>

## 📖 Sobre o Projeto
O Shadon Clone Bot vai além da simples cópia de canais e cargos. Ele foi projetado para realizar uma restauração de alta fidelidade da estrutura, permissões e configurações complexas de um servidor, incluindo a tela de Boas-vindas (Onboarding) e a reconfiguração de outros bots. É a solução ideal para criar backups, templates de servidores ou migrar uma comunidade com segurança.

## ✨ Principais Funcionalidades
* **Clonagem Estrutural Completa:** Salva e recria todas as categorias, canais de texto, canais de voz e cargos, mantendo a ordem e a hierarquia originais.
* **Permissões de Alta Fidelidade:** Copia não apenas as permissões gerais de cada cargo, mas também todas as permissões específicas (`overwrites`) de cada canal.
* **Clonagem de Fóruns com Tags:** Um dos poucos bots capazes de clonar canais de fórum e recriar todas as suas tags personalizadas.
* **Restauração das Configurações do Servidor:** Aplica configurações essenciais como o nome do servidor, canal de mensagens de sistema, canal de regras e configurações de ausência (AFK).
* **Suporte à Tela de Boas-Vindas (Onboarding):** Clona e restaura a complexa tela de "Onboarding" da comunidade.
* **Reconfiguração Inteligente de Bots:** Após a clonagem, um comando final aplica as permissões e cargos corretos a todos os outros bots que você convidar para o novo servidor.
* **Processo Modular e Seguro:** A clonagem é dividida em etapas, dando ao administrador controle total sobre o processo.

## ⚙️ Pré-requisitos e Configuração
Antes de começar, garanta que você tenha o Python 3.8 ou superior instalado.

1.  **Clone o repositório:**
    ```sh
    git clone [https://github.com/BioonsYT/Discord-Server-Cloner.git](https://github.com/BioonsYT/Discord-Server-Cloner.git)
    ```
2.  **Navegue até a pasta do projeto:**
    ```sh
    cd Discord-Server-Cloner
    ```
3.  **Instale as dependências:**
    ```sh
    pip install -r requirements.txt
    ```
4.  **Configure seu Token:**
    * Crie um arquivo chamado `.env` na pasta principal do projeto.
    * Dentro dele, adicione o token do seu bot, como no exemplo abaixo:
        ```
        DISCORD_TOKEN=SEU_TOKEN_SUPER_SECRETO_AQUI
        ```

## 🚀 Como Utilizar
O processo foi desenhado para ser robusto e sequencial. Siga os passos na ordem correta.

1.  **No servidor ORIGINAL (o que você quer copiar):**
    * Execute o comando `/clonar`. Isso irá gerar o arquivo de backup `template.json`.

2.  **No servidor de DESTINO (novo e vazio):**
    * **Passo 1:** Execute `/colar_estrutura` para criar a base de cargos e canais.
    * **Passo 2:** Execute `/colar_foruns` para criar os canais de fórum.
    * **Passo 3:** Execute `/colar_configuracoes` para aplicar o nome e as configurações gerais.
    * **Passo 4:** Execute `/colar_onboarding` para aplicar a tela de boas-vindas.
    * **Passo 5 (Opcional):** Use `/colar_booster` para sincronizar as permissões do cargo de Booster.

3.  **Finalização:**
    * Convide todos os outros bots (MEE6, Dyno, etc.) para o novo servidor.
    * Execute `/configurar_bots` para aplicar as permissões finais e concluir a clonagem.

## 🚧 Limitações Conhecidas
Por limitações da própria API do Discord, certas coisas não podem ser clonadas:

* **Histórico de Mensagens:** A API não permite que um bot poste mensagens em nome de outros usuários.
* **Membros e Cargos Atribuídos:** O bot não pode forçar membros a entrarem em um novo servidor.
* **Dados de Outros Bots:** Níveis (MEE6), economias, etc., são armazenados nos bancos de dados privados de cada bot e não podem ser acessados.

## 🧑‍💻 Desenvolvedor
Desenvolvido por [Bioons](https://github.com/BioonsYT)  
Versão atual: `v1.0`  
Licença: **Gratuito para uso >pessoal<**

## ❤️ Agradecimentos
Criado com 💻, ☕ e muita paciencia para fazer uma backup e clonagem completa do seu servidor.  
Se você curtiu o projeto, deixe uma ⭐ no repositório e compartilhe com seus amigos.

## 📄 Licença
Este projeto está sob a Licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
