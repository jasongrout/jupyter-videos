import os

base = os.environ["RV_BASE"]
c.ServerApp.root_dir = os.path.join(base, os.environ.get("RV_ROOT", "root"))
c.ServerApp.open_browser = False
c.ServerApp.port_retries = 0
c.IdentityProvider.token = ""
c.ServerApp.password = ""
c.LabApp.user_settings_dir = os.path.join(base, os.environ.get("RV_SETTINGS", "settings"))
c.LabApp.workspaces_dir = os.path.join(base, os.environ.get("RV_WORKSPACES", "workspaces"))
c.LabApp.expose_app_in_browser = True
c.TerminalManager.cull_inactive_timeout = 0
c.ServerApp.terminado_settings = {"shell_command": ["/bin/bash", "--norc", "--noprofile"]}
# Jupyter Notebook 7 reads its own app section.
c.JupyterNotebookApp.user_settings_dir = os.path.join(base, os.environ.get("RV_SETTINGS", "settings"))
c.JupyterNotebookApp.workspaces_dir = os.path.join(base, os.environ.get("RV_WORKSPACES", "workspaces"))
c.JupyterNotebookApp.expose_app_in_browser = True
