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
  python314.pkgs.black
  python314.pkgs.pandas
  python314.pkgs.django
  python314.pkgs.django-htmx
  python314.pkgs.django-filter
  # python314.pkgs.django-stubs
  python314.pkgs.mypy
  python314.pkgs.pytest
  ruff
  ];
}
