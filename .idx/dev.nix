# To learn more about how to use Nix to configure your environment
# see: https://developers.google.com/idx/guides/customize-idx-env
{ pkgs, ... }: {
  # Which nixpkgs channel to use.
  channel = "stable-24.05"; # or "unstable"

  # Use https://search.nixos.org/packages to find packages
  packages = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.python311Packages.pyngrok
  ];

  # Sets environment variables in the workspace
  env = {};

  idx = {
    # Search for the extensions you want on https://open-vsx.org/ and use "publisher.id"
    extensions = [
      # "vscodevim.vim"
    ];

    # Enable previews
    previews = {
      enable = false;
      previews = {
        web = {
          command = ["python" "manage.py" "runserver"];
          manager = "web";
        };
      };
    };

    # Workspace lifecycle hooks
    workspace = {
      # Runs when a workspace is first created
      onCreate = {
        # Create a virtual environment and install packages
        # setup = ''
        #   python -m venv .venv
        #   source .venv/bin/activate
        #   pip install -r requirements.txt
        # '';
      };
      # Runs when the workspace is (re)started
      # onStart = {
      #   # Activate the virtual environment
      #   init = "source .venv/bin/activate";
      # };
    };
  };
}