(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var modal = document.getElementById("modal-excluir");
        var botaoAbrir = document.getElementById("botao-excluir");
        var botaoCancelar = document.getElementById("botao-cancelar-exclusao");

        botaoAbrir.addEventListener("click", function () {
            modal.hidden = false;
        });
        botaoCancelar.addEventListener("click", function () {
            modal.hidden = true;
        });
    });
})();
