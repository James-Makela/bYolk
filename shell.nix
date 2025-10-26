{
  pkgs ? import <nixpkgs> { },
  packages ? [ ],
}:

with pkgs;
mkShell {
  packages = packages ++ [
  direnv
  nodejs
  python3.pkgs.black
  python3.pkgs.django
  python3.pkgs.django-filter
  python3.pkgs.django-stubs
  python3.pkgs.mypy
  python3.pkgs.pytest
  ruff
  ];
}
