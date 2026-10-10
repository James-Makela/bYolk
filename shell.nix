{
  pkgs ? import <nixpkgs> { },
  packages ? [ ],
}:

with pkgs;
let
  uv-fhs = buildFHSEnv {
    name = "uv";
    targetPkgs = _: [
      uv
      stdenv.cc.cc.lib
      zlib
      # add more libs here if a wheel fails to import
    ];
    runScript = "uv";
  };
in
mkShell {
  packages = packages ++ [
    nodejs
    uv-fhs
    podman
    podman-compose
  ];

  shellHook = ''
    export DOCKER_HOST="unix://$XDG_RUNTIME_DIR/podman/podman.sock"
    export PATH="$HOME/.local/bin:$PATH"

    # Set up registry config so short names resolve to Docker Hub
    export CONTAINERS_REGISTRIES_CONF=$PWD/.containers/registries.conf
    mkdir -p $PWD/.containers
    cat > $CONTAINERS_REGISTRIES_CONF <<EOF
    [registries.search]
    registries = ["docker.io", "quay.io", "ghcr.io"]
    EOF

    uv python install 3.14
    git config core.hooksPath .githooks
  '';
}
