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

    // Telefone: DDD é opcional. Sem DDD (até 9 dígitos) fica "9.8888-9999"
    // (ou "8888-9999" se for fixo, com só 8 dígitos); com DDD (10 ou 11
    // dígitos no total) acrescenta "(35) " na frente.
    function formatarTelefone(digitos) {
        digitos = digitos.slice(0, 11);
        var ddd = "";
        var numeroLocal = digitos;
        if (digitos.length > 9) {
            ddd = digitos.slice(0, 2);
            numeroLocal = digitos.slice(2);
        }

        var parteLocal;
        if (numeroLocal.length <= 8) {
            parteLocal = numeroLocal.length <= 4
                ? numeroLocal
                : numeroLocal.slice(0, 4) + "-" + numeroLocal.slice(4);
        } else {
            parteLocal = numeroLocal.slice(0, 1) + "." + numeroLocal.slice(1, 5) +
                (numeroLocal.length > 5 ? "-" + numeroLocal.slice(5) : "");
        }

        return ddd ? "(" + ddd + ") " + parteLocal : parteLocal;
    }

    function aplicarMascaraTelefone(input) {
        input.setAttribute("inputmode", "numeric");
        input.addEventListener("input", function () {
            var digitos = apenasDigitos(input.value).slice(0, 11);
            input.value = digitos ? formatarTelefone(digitos) : "";
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
            var descricao = linha.querySelector(".campo-descricao").value.trim();
            var preco = linha.querySelector(".campo-preco").value.trim();
            if ((descricao || preco) && !window.confirm("Remover este item?")) {
                return;
            }
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

    function inicializarClienteAutofill() {
        var nomeInput = document.getElementById("nome");
        var telInput = document.getElementById("tel");
        var cidadeInput = document.getElementById("cidade");

        nomeInput.addEventListener("change", function () {
            var clientes = window.SUGESTOES_CLIENTES || {};
            var dados = clientes[nomeInput.value.trim()];
            if (!dados) {
                return;
            }
            if (!telInput.value.trim() && dados.telefone) {
                telInput.value = dados.telefone;
            }
            if (!cidadeInput.value.trim() && dados.cidade) {
                cidadeInput.value = dados.cidade;
            }
            agendarRascunho();
        });
    }

    function escaparHtml(texto) {
        var div = document.createElement("div");
        div.textContent = texto || "";
        return div.innerHTML;
    }

    var VEICULO_COPIA_PASSO = 5;
    var resultadosVeiculoCopia = [];
    var quantidadeExibidaVeiculoCopia = VEICULO_COPIA_PASSO;
    var temporizadorVeiculoCopia = null;

    function itensContainerEstaVazio() {
        var vazio = true;
        document.querySelectorAll("#itens .campo-descricao").forEach(function (campo) {
            if (campo.value.trim()) {
                vazio = false;
            }
        });
        return vazio;
    }

    function copiarItensDoResultado(resultado) {
        if (!itensContainerEstaVazio() && !window.confirm("Isso substitui os itens já digitados. Continuar?")) {
            return;
        }

        var container = document.getElementById("itens");
        container.innerHTML = "";
        var modelo = document.getElementById("modelo-item");
        resultado.itens.forEach(function (item) {
            var fragmento = modelo.content.cloneNode(true);
            var linha = fragmento.querySelector(".item-linha");
            linha.querySelector(".campo-descricao").value = item.descricao || "";
            linha.querySelector(".campo-quantidade").value = item.quantidade || "1";
            linha.querySelector(".campo-preco").value = item.preco_formatado || "";
            container.appendChild(fragmento);
        });
        document.querySelectorAll("#itens .item-linha").forEach(aplicarMascarasNaLinha);
        recalcularTotais();
        agendarRascunho();

        resultadosVeiculoCopia = [];
        renderizarVeiculoCopia();
    }

    function renderizarVeiculoCopia() {
        var container = document.getElementById("veiculo-copia");
        var lista = document.getElementById("veiculo-copia-lista");
        var botaoMais = document.getElementById("veiculo-copia-mais");

        if (!resultadosVeiculoCopia.length) {
            container.hidden = true;
            lista.innerHTML = "";
            return;
        }

        container.hidden = false;
        lista.innerHTML = "";
        resultadosVeiculoCopia.slice(0, quantidadeExibidaVeiculoCopia).forEach(function (resultado) {
            var botao = document.createElement("button");
            botao.type = "button";
            botao.className = "veiculo-copia-item";
            botao.innerHTML =
                '<div class="veiculo-copia-item-veiculo">' + escaparHtml(resultado.veiculo) + "</div>" +
                '<div class="veiculo-copia-item-sub">' + escaparHtml(resultado.cliente_nome) + " · " + escaparHtml(resultado.data_formatada) + "</div>";
            botao.addEventListener("click", function () {
                copiarItensDoResultado(resultado);
            });
            lista.appendChild(botao);
        });

        botaoMais.hidden = quantidadeExibidaVeiculoCopia >= resultadosVeiculoCopia.length;
    }

    function buscarVeiculoCopia() {
        var veiculoInput = document.getElementById("veiculo");
        var texto = veiculoInput.value.trim();
        if (texto.length < 2 || !window.URL_BUSCAR_POR_VEICULO) {
            resultadosVeiculoCopia = [];
            renderizarVeiculoCopia();
            return;
        }

        var idInput = document.getElementById("orcamento-id");
        var excluirId = idInput ? idInput.value : "";
        var url = window.URL_BUSCAR_POR_VEICULO + "?veiculo=" + encodeURIComponent(texto) +
            (excluirId ? "&excluir_id=" + encodeURIComponent(excluirId) : "");

        fetch(url)
            .then(function (resposta) { return resposta.json(); })
            .then(function (dados) {
                resultadosVeiculoCopia = dados.resultados || [];
                quantidadeExibidaVeiculoCopia = VEICULO_COPIA_PASSO;
                renderizarVeiculoCopia();
            })
            .catch(function () {
                // falha de rede: só não mostra a sugestão, o resto do formulário segue normal.
            });
    }

    function inicializarVeiculoCopia() {
        var veiculoInput = document.getElementById("veiculo");
        veiculoInput.addEventListener("input", function () {
            window.clearTimeout(temporizadorVeiculoCopia);
            temporizadorVeiculoCopia = window.setTimeout(buscarVeiculoCopia, 350);
        });
        document.getElementById("veiculo-copia-mais").addEventListener("click", function () {
            quantidadeExibidaVeiculoCopia += VEICULO_COPIA_PASSO;
            renderizarVeiculoCopia();
        });
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
            var dados = coletarRascunho();
            dados.salvoEm = Date.now();
            window.localStorage.setItem(chaveRascunho(), JSON.stringify(dados));
            mostrarIndicadorRascunho();
        } catch (erro) {
            // localStorage indisponível (modo privado, por exemplo): ignora.
        }
        atualizarPreviewPdf();
    }

    // Pré-visualização do PDF ao lado do formulário: só existe em telas de
    // PC (ver breakpoint em static/css/style.css); no celular o elemento
    // nem aparece, então nem vale a pena gerar o PDF a cada edição.
    var LARGURA_MINIMA_PREVIEW = "(min-width: 900px)";
    var urlObjetoPreviewAtual = null;

    function atualizarPreviewPdf() {
        var iframe = document.getElementById("pdf-preview-form");
        if (!iframe || !window.URL_PRE_VISUALIZAR) {
            return;
        }
        if (!window.matchMedia(LARGURA_MINIMA_PREVIEW).matches) {
            return;
        }

        var form = document.getElementById("form-orcamento");
        fetch(window.URL_PRE_VISUALIZAR, { method: "POST", body: new FormData(form) })
            .then(function (resposta) {
                if (!resposta.ok) {
                    throw new Error("Falha ao gerar a pré-visualização.");
                }
                return resposta.blob();
            })
            .then(function (blob) {
                var novaUrl = URL.createObjectURL(blob);
                iframe.src = novaUrl;
                if (urlObjetoPreviewAtual) {
                    URL.revokeObjectURL(urlObjetoPreviewAtual);
                }
                urlObjetoPreviewAtual = novaUrl;
            })
            .catch(function () {
                // falha ao gerar a pré-visualização: ignora, o formulário
                // continua funcionando normalmente sem ela.
            });
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

        // Pra orçamento novo, a chave do rascunho não é por cliente — então,
        // se já tem algo digitado, confirma antes de restaurar (senão o
        // rascunho de um cliente anterior reaparece sozinho num orçamento
        // de outro cliente).
        var ehNovo = !document.getElementById("orcamento-id").value;
        var temConteudo = Boolean(
            (dados.nome && dados.nome.trim()) ||
            (dados.itens || []).some(function (item) {
                return item.descricao && item.descricao.trim();
            })
        );
        if (ehNovo && temConteudo) {
            var quando = dados.salvoEm
                ? new Date(dados.salvoEm).toLocaleString("pt-BR")
                : "";
            var mensagem = "Encontramos um rascunho não salvo" +
                (dados.nome ? ' de "' + dados.nome + '"' : "") +
                (quando ? " (" + quando + ")" : "") +
                ". Continuar esse rascunho?";
            if (!window.confirm(mensagem)) {
                limparRascunho();
                return;
            }
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
        inicializarClienteAutofill();
        inicializarVeiculoCopia();
        aplicarMascaraTelefone(document.getElementById("tel"));
        restaurarRascunho();

        var telInput = document.getElementById("tel");
        var digitosTelefoneAtual = apenasDigitos(telInput.value).slice(0, 11);
        if (digitosTelefoneAtual) {
            telInput.value = formatarTelefone(digitosTelefoneAtual);
        }

        recalcularTotais();
        atualizarPreviewPdf();

        ["nome", "cidade", "veiculo", "data"].forEach(function (id) {
            document.getElementById(id).addEventListener("input", agendarRascunho);
        });

        document.getElementById("form-orcamento").addEventListener("submit", function () {
            limparRascunho();
        });
    });
})();
