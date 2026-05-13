{
  pkgs ? import <nixpkgs> { },
  packages ? [ ],
}:

with pkgs;
mkShell {
  packages = packages ++ [
  direnv
  nodejs
  sqlite
  python314
  podman
  podman-compose
  ];

  # Required to run numpy from the venv environment
  NIX_LD_LIBRARY_PATH = lib.makeLibraryPath [
    stdenv.cc.cc
  ];
  NIX_LD = lib.fileContents "${stdenv.cc}/nix-support/dynamic-linker";
  shellHook = ''
    export LD_LIBRARY_PATH=$NIX_LD_LIBRARY_PATH
    export DOCKER_HOST="unix://$XDG_RUNTIME_DIR/podman/podman.sock"

    # Set up registry config so short names resolve to Docker Hub
    export CONTAINERS_REGISTRIES_CONF=$PWD/.containers/registries.conf
    mkdir -p $PWD/.containers
    cat > $CONTAINERS_REGISTRIES_CONF <<EOF
    [registries.search]
    registries = ["docker.io", "quay.io", "ghcr.io"]
    EOF

    podman system service --time=0 unix://$XDG_RUNTIME_DIR/podman/podman.sock &
  '';
}
