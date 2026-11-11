(function () {
    "use strict";

    function inicializarExclusao() {
        var modal = document.getElementById("modal-excluir");
        var botaoAbrir = document.getElementById("botao-excluir");
        var botaoCancelar = document.getElementById("botao-cancelar-exclusao");
        if (!botaoAbrir) {
            return;
        }

        botaoAbrir.addEventListener("click", function () {
            modal.hidden = false;
        });
        botaoCancelar.addEventListener("click", function () {
            modal.hidden = true;
        });
    }

    function inicializarWhatsapp() {
        var botao = document.getElementById("botao-whatsapp");
        if (!botao) {
            return;
        }

        var urlPdf = botao.dataset.urlPdf;
        var urlMarcarEnviado = botao.dataset.urlMarcarEnviado;
        var csrfToken = botao.dataset.csrf;
        var nomeArquivo = botao.dataset.nomeArquivo;
        var status = document.getElementById("whatsapp-status");

        function mostrarStatus(texto, erro) {
            status.textContent = texto;
            status.hidden = false;
            status.classList.toggle("texto-status-erro", !!erro);
        }

        function baixarArquivo(blob, nome) {
            var url = URL.createObjectURL(blob);
            var link = document.createElement("a");
            link.href = url;
            link.download = nome;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.setTimeout(function () {
                URL.revokeObjectURL(url);
            }, 1000);
        }

        function marcarComoEnviado() {
            return fetch(urlMarcarEnviado, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: "csrf_token=" + encodeURIComponent(csrfToken)
            }).then(function (resposta) {
                if (!resposta.ok) {
                    throw new Error("Falha ao registrar o envio.");
                }
                return resposta.json();
            });
        }

        botao.addEventListener("click", function () {
            botao.disabled = true;
            mostrarStatus("Preparando o PDF...");

            fetch(urlPdf)
                .then(function (resposta) {
                    if (!resposta.ok) {
                        throw new Error("Falha ao gerar o PDF.");
                    }
                    return resposta.blob();
                })
                .then(function (blob) {
                    var arquivo = null;
                    try {
                        arquivo = new File([blob], nomeArquivo, { type: "application/pdf" });
                    } catch (erroArquivo) {
                        arquivo = null;
                    }

                    var podeCompartilharArquivo =
                        arquivo &&
                        typeof navigator.canShare === "function" &&
                        navigator.canShare({ files: [arquivo] });

                    if (podeCompartilharArquivo) {
                        status.hidden = true;
                        return navigator
                            .share({ files: [arquivo] })
                            .then(marcarComoEnviado)
                            .then(function (dados) {
                                mostrarStatus("Enviado em " + dados.enviado_em_formatado + ".");
                                window.setTimeout(function () {
                                    window.location.reload();
                                }, 900);
                            })
                            .catch(function (erro) {
                                if (erro && erro.name === "AbortError") {
                                    status.hidden = true;
                                    return;
                                }
                                mostrarStatus("Não deu para compartilhar. Tente de novo.", true);
                            });
                    }

                    // Sem suporte a compartilhar arquivo (navegador antigo ou
                    // desktop): baixa o PDF e orienta a anexar na mão.
                    baixarArquivo(blob, nomeArquivo);
                    return marcarComoEnviado().then(function (dados) {
                        mostrarStatus(
                            "PDF baixado (" +
                                dados.enviado_em_formatado +
                                "). Abra o WhatsApp e anexe o arquivo baixado."
                        );
                    });
                })
                .catch(function () {
                    mostrarStatus("Não deu para gerar o PDF agora. Tente de novo.", true);
                })
                .finally(function () {
                    botao.disabled = false;
                });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        inicializarExclusao();
        inicializarWhatsapp();
    });
})();
