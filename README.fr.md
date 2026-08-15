# Wisp MCP — connecter un panel WISP à une IA

**[English](README.md) · Français**

Wisp MCP est un serveur Model Context Protocol (MCP) source-available pour l’**API Client du panel WISP**. Il permet à un client IA compatible MCP d’inspecter et d’administrer un serveur de jeu via le panel, sans donner à l’IA un accès système illimité à la machine de l’hébergeur.

Le projet est **indépendant de l’hébergeur** : si ton hébergeur fournit un panel WISP et un token Client API, tu utilises simplement l’URL de ce panel.

[![CI](https://github.com/BreezeDelegate/wisp-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/BreezeDelegate/wisp-mcp/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/BreezeDelegate/wisp-mcp)](https://github.com/BreezeDelegate/wisp-mcp/releases/latest)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-active-2ea44f)](https://registry.modelcontextprotocol.io/?q=io.github.BreezeDelegate%2Fwisp-mcp)

**Guide visuel en français :** https://breezedelegate.github.io/wisp-mcp/fr/

## Est-ce que mon panel est WISP ?

Si ton interface ressemble à ceci, il s’agit probablement de WISP :

![Exemple de panel client WISP](docs/assets/wisp-client-panel.webp)

Les hébergeurs peuvent changer le logo, les couleurs et le domaine. En cas de doute, demande simplement au support : **« Mon serveur utilise-t-il WISP et puis-je créer un token WISP Client API ? »**

## Ce que Wisp MCP peut faire

- lire l’état du serveur, CPU, RAM, disque et réseau ;
- parcourir les dossiers avec pagination et lire les configurations/logs ;
- rechercher dans de gros fichiers sans envoyer tout le fichier au modèle ;
- lire des morceaux bornés avec `read_file_chunk` ;
- modifier de gros plugins/configs de façon ciblée avec `replace_in_file` ;
- protéger les écritures existantes par SHA-256 avec `safe_write_file` ;
- envoyer des commandes console ;
- démarrer, arrêter et redémarrer le serveur ;
- créer et inspecter les sauvegardes ;
- gérer les bases de données lorsque la permission est activée ;
- fonctionner en local avec **stdio** ou à distance avec **Streamable HTTP**.

Les opérations destructrices restent derrière une permission distincte.

## Installation sur un VPS Linux

Pour Debian 12 ou Ubuntu 24.04+ :

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash
```

L’installateur demande directement dans le terminal :

1. l’URL de ton panel WISP ;
2. éventuellement l’identifiant du serveur par défaut ;
3. ton token WISP Client API dans un prompt masqué.

Il crée un utilisateur système dédié, stocke les secrets hors de Git et vérifie la connexion avec `wisp-mcp doctor`.

Pour vérifier plus profondément que l’API WISP reste compatible sans rien modifier :

```bash
wisp-mcp compatibility
```

### ChatGPT

Pour installer également l’assistant de tunnel MCP privé OpenAI :

```bash
curl -fsSL https://raw.githubusercontent.com/BreezeDelegate/wisp-mcp/main/install-vps.sh | sudo bash -s -- --with-openai
```

Le tunnel et l’app ChatGPT sont ensuite configurés séparément. Voir la [documentation ChatGPT](docs/chatgpt.md).

### Claude Code

Claude Code peut lancer Wisp MCP directement. Si le MCP tourne sur un VPS distant :

```bash
claude mcp add --scope user wisp -- ssh user@ton-vps /usr/local/bin/wisp-mcp-stdio
```

Puis :

```bash
claude mcp get wisp
```

### Autres clients MCP

Wisp MCP utilise les transports MCP standards :

- **stdio** pour un client local ou via SSH ;
- **Streamable HTTP** derrière authentification ;
- **MCP Bundle (`.mcpb`)** pour les clients qui prennent ce format en charge.

## Permissions

Les écritures sont désactivées par défaut :

```env
WISP_ALLOW_COMMANDS=true
WISP_ALLOW_FILE_WRITES=true
WISP_ALLOW_POWER=true
WISP_ALLOW_BACKUPS=true
WISP_ALLOW_DATABASES=false
WISP_ALLOW_SERVER_SETTINGS=false
WISP_ALLOW_DESTRUCTIVE=false
```

Pour une administration normale, conserve `WISP_ALLOW_DESTRUCTIVE=false`.

## Gros fichiers et modifications sûres

L optimisation du contexte est adaptative : elle ne doit jamais reduire la comprehension necessaire a une modification fiable. Si le changement depend d un etat global, de hooks eloignes, de classes partagees, du flux de controle ou d interactions dans l ensemble du fichier, une lecture complete est preferable meme si elle consomme davantage de tokens.

Pour un gros plugin, évite `read_file` sur tout le fichier quand ce n’est pas nécessaire :

- `find_in_file` localise une chaîne et renvoie seulement quelques lignes autour ;
- `read_file_chunk` renvoie une plage bornée et indique `next_offset_chars` ;
- `file_fingerprint` renvoie SHA-256, taille et nombre de lignes sans contenu.

Les lectures texte incluent aussi leur SHA-256. Pour modifier un fichier existant :

- `replace_in_file` est recommandé pour une petite modification ciblée ;
- `safe_write_file` sert lorsqu’un remplacement complet est réellement voulu.

Ces outils relisent le fichier avant l’écriture et vérifient le résultat ensuite. Si le SHA-256 a changé depuis la lecture précédente, l’écriture est refusée et l’IA doit relire le fichier.

## Sécurité

- les tokens API/MCP ne sont jamais retournés par les outils ;
- les chemins et identifiants sont validés ;
- les écritures sont limitées en taille ;
- les permissions sensibles sont opt-in ;
- l’accès HTTP distant échoue fermé si l’authentification n’est pas configurée ;
- les opérations destructrices ont leur propre garde-fou.

Le serveur indique aussi aux clients MCP d’inspecter avant modification, sauvegarder avant les changements risqués et vérifier les logs après intervention.

## Distribution

Wisp MCP est publié dans le **registre MCP officiel** sous :

`io.github.BreezeDelegate/wisp-mcp`

Les releases contiennent le wheel Python, les sources et un bundle `.mcpb`.

## Documentation technique

La documentation technique de référence reste en anglais afin d’éviter des versions divergentes :

- [Getting started](docs/getting-started.md)
- [Reconnaître WISP](docs/panel-recognition.md)
- [Compatibilité des clients IA](docs/clients.md)
- [ChatGPT / OpenAI Secure MCP Tunnel](docs/chatgpt.md)
- [Opérations et sécurité](docs/operations.md)

## Licence

Wisp MCP est distribué sous [PolyForm Noncommercial License 1.0.0](LICENSE). Un usage commercial nécessite une autorisation séparée du détenteur des droits.
