(function () {
    "use strict";

    function apenasDigitos(texto) {
        return (String(texto).match(/\d/g) || []).join("");
    }

    function formatarCentavos(digitos) {
        digitos = digitos.replace(/^0+(?=\d)/, "");
        while (digitos.length < 3) {
            digitos = "0" + digitos;
        }
        var centavos = digitos.slice(-2);
        var inteiros = digitos.slice(0, -2).replace(/^0+(?=\d)/, "");
        inteiros = inteiros.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
        return inteiros + "," + centavos;
    }

    function centavosDeTextoColado(texto) {
        texto = (texto || "").trim().replace(/[^\d.,]/g, "");
        if (!texto) {
            return 0;
        }
        var pos = Math.max(texto.lastIndexOf(","), texto.lastIndexOf("."));
        var inteiroStr, centavosStr;
        if (pos === -1) {
            inteiroStr = texto.replace(/[.,]/g, "");
            centavosStr = "00";
        } else {
            centavosStr = (texto.slice(pos + 1).replace(/\D/g, "") + "00").slice(0, 2);
            inteiroStr = texto.slice(0, pos).replace(/\D/g, "");
        }
        inteiroStr = inteiroStr.replace(/^0+(?=\d)/, "") || "0";
        return parseInt(inteiroStr, 10) * 100 + parseInt(centavosStr, 10);
    }

    function paraCentavos(valorFormatado) {
        var digitos = apenasDigitos(valorFormatado || "");
        return digitos ? parseInt(digitos, 10) : 0;
    }

    function aplicarMascaraDinheiro(input) {
        input.setAttribute("inputmode", "numeric");
        input.addEventListener("input", function () {
            var digitos = apenasDigitos(input.value).slice(0, 9);
            input.value = digitos ? formatarCentavos(digitos) : "";
            recalcularTotais();
            agendarRascunho();
        });
        input.addEventListener("paste", function (evento) {
            evento.preventDefault();
            var dados = evento.clipboardData || window.clipboardData;
            var texto = dados ? dados.getData("text") : "";
            var centavos = centavosDeTextoColado(texto);
            input.value = centavos ? formatarCentavos(String(centavos)) : "";
            recalcularTotais();
            agendarRascunho();
        });
    }

    function aplicarMascaraQuantidade(input) {
        input.setAttribute("inputmode", "numeric");
        input.addEventListener("input", function () {
            var digitos = apenasDigitos(input.value).replace(/^0+(?=\d)/, "").slice(0, 3);
            input.value = digitos;
            recalcularTotais();
            agendarRascunho();
        });
    }

    function formatarReais(centavos) {
        return formatarCentavos(String(Math.max(0, centavos)));
    }

    function recalcularTotais() {
        var subtotal = 0;
        document.querySelectorAll("#itens .item-linha").forEach(function (linha) {
            var qtd = parseInt(linha.querySelector(".campo-quantidade").value || "1", 10) || 0;
            var preco = paraCentavos(linha.querySelector(".campo-preco").value);
            var total = qtd * preco;
            linha.querySelector(".item-total").textContent = "R$ " + formatarReais(total);
            subtotal += total;
        });

        var bombaIncluidaInput = document.getElementById("bomba-incluida");
        var bombaTotal = 0;
        if (bombaIncluidaInput && bombaIncluidaInput.value === "1") {
            var qtdBomba = parseInt(document.getElementById("bomba_quantidade").value || "1", 10) || 0;
            var precoBomba = paraCentavos(document.getElementById("bomba_preco").value);
            bombaTotal = qtdBomba * precoBomba;
            document.getElementById("bomba-total-exibicao").textContent = "R$ " + formatarReais(bombaTotal);
        }

        var subtotalEl = document.getElementById("subtotal-exibicao");
        var totalEl = document.getElementById("total-exibicao");
        if (subtotalEl) {
            subtotalEl.textContent = "R$ " + formatarReais(subtotal);
        }
        if (totalEl) {
            totalEl.textContent = "R$ " + formatarReais(subtotal + bombaTotal);
        }
    }

    function aplicarMascarasNaLinha(linha) {
        aplicarMascaraQuantidade(linha.querySelector(".campo-quantidade"));
        aplicarMascaraDinheiro(linha.querySelector(".campo-preco"));
        var descricaoInput = linha.querySelector(".campo-descricao");
        descricaoInput.addEventListener("input", agendarRascunho);
        descricaoInput.addEventListener("change", function () {
            var chave = descricaoInput.value.trim();
            var precoInput = linha.querySelector(".campo-preco");
            var sugestoes = window.SUGESTOES_ITENS || {};
            if (chave && !precoInput.value && Object.prototype.hasOwnProperty.call(sugestoes, chave)) {
                precoInput.value = formatarCentavos(String(sugestoes[chave]));
                recalcularTotais();
                agendarRascunho();
            }
        });
        linha.querySelector(".botao-remover-item").addEventListener("click", function () {
            linha.remove();
            recalcularTotais();
            agendarRascunho();
        });
    }

    function inicializarItens() {
        document.querySelectorAll("#itens .item-linha").forEach(aplicarMascarasNaLinha);

        var modelo = document.getElementById("modelo-item");
        document.getElementById("botao-adicionar-item").addEventListener("click", function () {
            var fragmento = modelo.content.cloneNode(true);
            var linha = fragmento.querySelector(".item-linha");
            document.getElementById("itens").appendChild(fragmento);
            aplicarMascarasNaLinha(linha);
            linha.querySelector(".campo-descricao").focus();
            agendarRascunho();
        });
    }

    function inicializarBomba() {
        var botao = document.getElementById("bomba-toggle");
        var input = document.getElementById("bomba-incluida");
        var campos = document.getElementById("bomba-campos");
        var aviso = document.getElementById("bomba-aviso");

        botao.addEventListener("click", function () {
            var ligado = input.value !== "1";
            input.value = ligado ? "1" : "0";
            botao.setAttribute("aria-checked", ligado ? "true" : "false");
            botao.classList.toggle("switch-ligado", ligado);
            campos.hidden = !ligado;
            aviso.hidden = ligado;
            recalcularTotais();
            agendarRascunho();
        });

        aplicarMascaraQuantidade(document.getElementById("bomba_quantidade"));
        aplicarMascaraDinheiro(document.getElementById("bomba_preco"));
        document.getElementById("bomba_descricao").addEventListener("input", agendarRascunho);
    }

    function coletarItens() {
        var itens = [];
        document.querySelectorAll("#itens .item-linha").forEach(function (linha) {
            itens.push({
                descricao: linha.querySelector(".campo-descricao").value,
                quantidade: linha.querySelector(".campo-quantidade").value,
                preco: linha.querySelector(".campo-preco").value
            });
        });
        return itens;
    }

    function coletarRascunho() {
        return {
            nome: document.getElementById("nome").value,
            telefone: document.getElementById("tel").value,
            cidade: document.getElementById("cidade").value,
            veiculo: document.getElementById("veiculo").value,
            data: document.getElementById("data").value,
            bombaIncluida: document.getElementById("bomba-incluida").value,
            bombaDescricao: document.getElementById("bomba_descricao").value,
            bombaQuantidade: document.getElementById("bomba_quantidade").value,
            bombaPreco: document.getElementById("bomba_preco").value,
            itens: coletarItens()
        };
    }

    function chaveRascunho() {
        var id = document.getElementById("orcamento-id").value;
        return "rascunho_orcamento_" + (id || "novo");
    }

    function mostrarIndicadorRascunho() {
        var indicador = document.getElementById("indicador-rascunho");
        if (indicador) {
            indicador.hidden = false;
        }
    }

    function salvarRascunho() {
        try {
            window.localStorage.setItem(chaveRascunho(), JSON.stringify(coletarRascunho()));
            mostrarIndicadorRascunho();
        } catch (erro) {
            // localStorage indisponível (modo privado, por exemplo): ignora.
        }
    }

    var temporizadorRascunho = null;
    function agendarRascunho() {
        window.clearTimeout(temporizadorRascunho);
        temporizadorRascunho = window.setTimeout(salvarRascunho, 600);
    }

    function restaurarRascunho() {
        var bruto;
        try {
            bruto = window.localStorage.getItem(chaveRascunho());
        } catch (erro) {
            return;
        }
        if (!bruto) {
            return;
        }
        var dados;
        try {
            dados = JSON.parse(bruto);
        } catch (erro) {
            return;
        }

        document.getElementById("nome").value = dados.nome || "";
        document.getElementById("tel").value = dados.telefone || "";
        document.getElementById("cidade").value = dados.cidade || "";
        document.getElementById("veiculo").value = dados.veiculo || "";
        if (dados.data) {
            document.getElementById("data").value = dados.data;
        }

        var bombaIncluida = dados.bombaIncluida === "1";
        var botaoBomba = document.getElementById("bomba-toggle");
        document.getElementById("bomba-incluida").value = bombaIncluida ? "1" : "0";
        botaoBomba.setAttribute("aria-checked", bombaIncluida ? "true" : "false");
        botaoBomba.classList.toggle("switch-ligado", bombaIncluida);
        document.getElementById("bomba-campos").hidden = !bombaIncluida;
        document.getElementById("bomba-aviso").hidden = bombaIncluida;
        document.getElementById("bomba_descricao").value = dados.bombaDescricao || "";
        document.getElementById("bomba_quantidade").value = dados.bombaQuantidade || "1";
        document.getElementById("bomba_preco").value = dados.bombaPreco || "";

        if (dados.itens && dados.itens.length) {
            var container = document.getElementById("itens");
            container.innerHTML = "";
            var modelo = document.getElementById("modelo-item");
            dados.itens.forEach(function (item) {
                var fragmento = modelo.content.cloneNode(true);
                var linha = fragmento.querySelector(".item-linha");
                linha.querySelector(".campo-descricao").value = item.descricao || "";
                linha.querySelector(".campo-quantidade").value = item.quantidade || "1";
                linha.querySelector(".campo-preco").value = item.preco || "";
                container.appendChild(fragmento);
            });
            document.querySelectorAll("#itens .item-linha").forEach(aplicarMascarasNaLinha);
        }

        mostrarIndicadorRascunho();
        recalcularTotais();
    }

    function limparRascunho() {
        try {
            window.localStorage.removeItem(chaveRascunho());
        } catch (erro) {
            // ignora
        }
    }

    document.addEventListener("DOMContentLoaded", function () {
        inicializarItens();
        inicializarBomba();
        restaurarRascunho();
        recalcularTotais();

        ["nome", "tel", "cidade", "veiculo", "data"].forEach(function (id) {
            document.getElementById(id).addEventListener("input", agendarRascunho);
        });

        document.getElementById("form-orcamento").addEventListener("submit", function () {
            limparRascunho();
        });
    });
})();
