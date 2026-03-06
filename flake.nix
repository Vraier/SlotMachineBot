{
  description = "Python environment for the Blue Prince Slot Machine Bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" ];
      forEachSystem = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      devShells = forEachSystem (system:
        let
          pkgs = import nixpkgs { inherit system; };
          
          # Removed mss
          pythonEnv = pkgs.python3.withPackages (ps: with ps; [
            opencv4
            numpy
            matplotlib
          ]);
        in
        {
          default = pkgs.mkShell {
            packages = [
              pythonEnv
              pkgs.grim # for screenshots
              pkgs.ydotool # for mouse clicking
            ];
          };
        }
      );
    };
}