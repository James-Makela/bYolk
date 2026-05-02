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
  djhtml
  python313.pkgs.black
  python313.pkgs.pandas
  python313.pkgs.django
  python313.pkgs.django-htmx
  python313.pkgs.django-filter
  python313.pkgs.mypy
  python313.pkgs.pytest
  ruff
  ];
}
