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
  python314.pkgs.pandas
  python314
  ];
}
