{
  pkgs ? import <nixpkgs> { },
  packages ? [ ],
}:

with pkgs;
mkShell {
  packages = packages ++ [
  python3.pkgs.pytest
  python3.pkgs.mypy
  python3.pkgs.django
  ruff
  direnv
  python3.pkgs.django-stubs
  ];
}
