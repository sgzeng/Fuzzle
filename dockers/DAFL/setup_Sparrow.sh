cd /home/maze/
git clone https://github.com/prosyslab/sparrow.git

cd /home/maze/sparrow
git checkout dafl
export OPAMYES=1

sed -i '/^opam init/ s/$/ --disable-sandboxing/' build.sh
./build.sh
opam init --disable-sandboxing -y && eval $(opam env)
opam install ppx_compare yojson ocamlgraph memtrace lymp clangml conf-libclang.13 batteries apron conf-mpfr cil linenoise claml

eval $(opam env)
make clean
make
