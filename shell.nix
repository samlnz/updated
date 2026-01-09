{ pkgs ? import <nixpkgs> {} }:
  pkgs.mkShell {
    buildInputs = with pkgs.python3Packages; [
      python
      pip
      flask
      flask-sqlalchemy
      psycopg2
      # Add other dependencies from requirements.txt here
    ];
  }
