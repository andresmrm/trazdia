#!/usr/bin/env python
# -*- coding: utf8 -*-

#-----------------------------------------------------------------------------
# Copyright 2009 Andrés Mantecon Ribeiro Martano
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#-----------------------------------------------------------------------------

import sys
import subprocess
from subprocess import Popen
import os
import datetime
import pickle
from threading import Thread
import time

# Bibliotecas para a interface gráfica
try:
    import pygtk
    pygtk.require("2.0")
except:
    print("Erro ao tentar importar PyGTK...")
    sys.exit(1)

try:
    import gtk
    import gtk.glade
except:
    print("Erro ao tentar importar GTK...")
    sys.exit(1)
    
try:
    import gobject
except:
    print("Erro ao tentar importar Gobject...")
    sys.exit(1)
    


LOGS = []
def documentar(texto):
    global LOGS
    LOGS.append(texto)
    

# Executa um comando através do SO
def comandar(comando):
    # Faz com que não apareça uma janela de terminal no M$ Windows
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    
    p = Popen(comando, stderr=subprocess.STDOUT, stdout=subprocess.PIPE,
        startupinfo=startupinfo)
    out, err = p.communicate()
    return (out, err)
#    documentar(out)
    

def date_texto(data):
    return str(data.year).zfill(4) + "/" + str(data.month).zfill(2)\
            + "/" + str(data.day).zfill(2)

def date_texto2(data):
    return str(data.day).zfill(2) + "/" + str(data.month).zfill(2)\
            + "/" + str(data.year).zfill(4)

def texto_date(data):
    dia, mes, ano = data.split("/")
    return datetime.date(int(ano), int(mes), int(dia))

def inverter_data(data):
    x, mes, x2 = data.split("/")
    return x2 + "/" + mes + "/" + x

def montar_nome_arquivo(pasta, data, secao, pagina, extensao):
    return os.path.join(pasta, str(secao) + "_" + str(pagina) + '.' + extensao)
    

# Converte um arquivo de PDF para texto puro
def converter_pdf(nome_arquivo):
    comandar(["pdftotext", nome_arquivo])
    

# Verifica se naquele dia deveria haver jornal
def verificar_se_dia_com_jornal(data):
    
    dia_semana = texto_date(data).weekday()
    
    if dia_semana == 5 or dia_semana == 6:
        return False
    else:
        return True
    

# Realiza a pesquisa
class buscador():
    
    def __init__(self, nome):
        self.palavras_procuradas = []
        self.nome = nome
        
    
    def adicionar(self, pal):
        self.palavras_procuradas.append(pal)
        
    
    def trocar(self, palavras):
        self.palavras_procuradas = palavras
        
    
    def salvar(self, nome_arquivo=None):
        if not nome_arquivo:
            nome_arquivo = self.nome
            
        try:
            arq = open(nome_arquivo, "w")
            for linha in self.palavras_procuradas:
                arq.write(linha + "\n")
            arq.close()
        except:
            print("Não foi possível salvar o arquivo do buscador!")
        
    
    def carregar(self, nome_arquivo=None):
        if not nome_arquivo:
            nome_arquivo = self.nome
            
        try:
            arq = open(nome_arquivo, "r")
            texto = arq.read()
            arq.close()
            texto = texto.splitlines()
            for linha in texto:
                self.adicionar(linha)
        except:
            print("Arquivo do buscador não encontrado!")
        

    def analisar(self, texto):
        
        ocorrencias = []
        
        for palavra in self.palavras_procuradas:
            
            posicao = 0
            while posicao != -1:
                posicao = texto.find(palavra, posicao)
            
                if posicao != -1:
                    ocorrencias.append((palavra, posicao))
                    posicao += 1
            
        return ocorrencias
        


class jornal():
    
    numero_de_secoes = 0
    por_data = True
    
    def __init__(self, data, pasta, monitor):
        self.data = data
        self.pasta = pasta
        self.teve_jornal = True
        
        self.ocorrencias = {}
        
        self.tam_secoes = []
        
        self.monitor = monitor
        
        for i in range(self.numero_de_secoes):
            self.tam_secoes.append(-1)
            
        #if not verificar_se_dia_com_jornal(self.data):
            #self.teve_jornal = False
            #print "Parece q esse dia não deveria ter tido jornal..."
            
    def baixar_pagina(self, num_secao, num_pagina, data, nome_arquivo):
        pass
        
    def obter_num_paginas_secao(self, num_secao, data, nome_arquivo):
        pass
    
    # Obtem a data e os tamanhos das seções do jornal na pasta
    def ler_dados(self):
        arq = open(os.path.join(self.pasta, "dados"), "r")
        texto = arq.read()
        arq.close()
        texto = texto.split()
        data = texto.pop(0)
        for linha in texto:
            self.tam_secoes[int(linha)] = int(linha)
    
    # Salva um arquivo com os tamanhos das seções
    def salvar_dados(self):
        arq = open(os.path.join(self.pasta, "dados"), "w")
        arq.write(self.data)
        for i in self.tam_secoes:
            arq.write(" " + str(i))
        arq.close()
    
    # Obtem informações sobre o jornal
    def obter_info(self):       
        for num_secao in range(1, self.numero_de_secoes + 1):
            
            if self.monitor.para:
                    return None
            
            self.tam_secoes[num_secao - 1] = \
                self.obter_num_paginas_secao(num_secao, self.data)
                
    # Baixa o jornal
    def baixar(self):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                nome = montar_nome_arquivo(self.pasta, self.data, num_secao,
                                           num_pagina, 'pdf')
                
                # Isso deve fazer com que PDFs que não foram terminados de 
                #baixar sejam deletados
                try:
                    arq = open(os.path.join(self.pasta, "baixando"), "r")
                    nome2 = arq.read()
                    os.remove(nome2)
                    arq.close()
                    os.remove(os.path.join(self.pasta, "baixando"))
                except:
                    print "Erro remover nao terminado"
                    pass
                
                arq = open(os.path.join(self.pasta, "baixando"), "w")
                arq.write(nome)
                arq.close()
                
                self.baixar_pagina(num_secao, num_pagina, self.data, nome)
                
                os.remove(os.path.join(self.pasta, "baixando"))
                    
    
    # Extrai os textos do jornal e deixa na mesma pasta
    def extrair_textos(self):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                nome = montar_nome_arquivo(self.pasta, self.data,
                                            num_secao, num_pagina, "pdf")
                documentar(nome)
                converter_pdf(nome)
                
    # Aplica o buscador no texto
    def analisar(self, buscador):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                nome = montar_nome_arquivo(self.pasta, self.data,
                                           num_secao, num_pagina, "txt")
                documentar(nome)
                
                try:
                    arq = open(nome)
                    texto = arq.read()
                    arq.close()
                    
                    ocorrencias_na_pagina = buscador.analisar(texto)
                    
                    if len(ocorrencias_na_pagina) != 0:
                        self.ocorrencias[(num_secao, num_pagina)] = \
                            ocorrencias_na_pagina
                except:
                    documentar("----->Erro ao tentar abrir esse arquivo!<-----")
                    
    # Remove os pdfs que não tiverem nenhuma ocorrencia na busca
    def remover_pdfs_nao_usados(self):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                if not self.ocorrencias.get((num_secao, num_pagina)):
                    os.remove(montar_nome_arquivo(self.pasta, self.data,
                                                   num_secao, num_pagina, "pdf"))
                    
    # Remove os txt que não tiverem nenhuma ocorrencia na busca
    def remover_txts_nao_usados(self):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                if not self.ocorrencias.get((num_secao, num_pagina)):
                    os.remove(montar_nome_arquivo(self.pasta, self.data,
                                                   num_secao, num_pagina, "txt"))
                    
    # Remove todos os arquivos do jornal
    def remover(self):
        for arq in os.listdir(self.pasta):
            os.remove(os.path.join(self.pasta, arq))
            
    # Executa as operações necessárias para baixar e processar um jornal
    def executar(self, buscador):
        documentar("Obtendo Dados")
        self.obter_info()
        if self.monitor.para:
            return []
        documentar("Baixando PDFs")
        self.baixar()
        if self.monitor.para:
            return []
        documentar("Extraindo Textos")
        self.extrair_textos()
        if self.monitor.para:
            return []
        documentar("Analisando Textos")
        self.analisar(buscador)
        if self.monitor.para:
            return []
        return self.ocorrencias
        




class Diario_Justica_do_MT(jornal):

    nome = "Diario_Justica_do_MT"
    numero_de_secoes = 1
    por_data = False

    # Baixa uma página de uma seção de uma data de jornal e coloca em uma pasta
    def baixar_pagina(self, num_secao, num_pagina, data, nome_arquivo):
        
        edicao = data
        ano = 2007
        
        baixou = False
        
        while not baixou:
            pagina_jornal = 'http://dje.tj.mt.gov.br/PDFDJE/'\
                            + str(edicao) + '-' + str(ano) + '.pdf'
                
            comando = ['wget', '-nc', '--output-document=' + nome_arquivo,
                        pagina_jornal]
            
            out, err = comandar(comando)

            # SO FUNCIONA PARA ANO <= 2020 =P (BUG DO VINTENIO)
            # Como o mundo acaba em 2012, da nada nao
            if out.find("ERRO 404: Not Found") != -1 and ano <= 2020:
                ano += 1
                try:
                    os.remove(nome_arquivo)
                except:
                    pass
            else:
                baixou = True
        
    def obter_num_paginas_secao(self, num_secao, data):
        return 1
    
    # Extrai os textos do jornal e deixa na mesma pasta
    def extrair_textos(self):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                nome = os.path.join(self.pasta, str(self.data) + ".pdf")
                documentar(nome)
                converter_pdf(nome)
    
        # Remove os pdfs que não tiverem nenhuma ocorrencia na busca
    def remover_pdfs_nao_usados(self):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                if not self.ocorrencias.get((num_secao, num_pagina)):
                    os.remove(os.path.join(self.pasta, str(self.data) + ".pdf"))
                    
    # Remove os txt que não tiverem nenhuma ocorrencia na busca
    def remover_txts_nao_usados(self):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                if not self.ocorrencias.get((num_secao, num_pagina)):
                    os.remove(os.path.join(self.pasta, str(self.data) + ".txt"))
    
    # Aplica o buscador no texto
    def analisar(self, buscador):
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                nome = os.path.join(self.pasta, str(self.data) + ".pdf")
                
                documentar(nome)
                
                try:
                    arq = open(nome)
                    texto = arq.read()
                    arq.close()
                    
                    ocorrencias_na_pagina = buscador.analisar(texto)
                    
                    if len(ocorrencias_na_pagina) != 0:
                        self.ocorrencias[(num_secao, num_pagina)] = \
                            ocorrencias_na_pagina
                except:
                    documentar("----->Erro ao tentar abrir esse arquivo!<-----")
    
    # Baixa o jornal
    def baixar(self):        
        for num_secao in range(1, self.numero_de_secoes + 1):
            for num_pagina in range(1, self.tam_secoes[num_secao - 1] + 1):
                
                if self.monitor.para:
                    return None
                
                nome = os.path.join(self.pasta, str(self.data) + ".pdf")
                
                # Isso deve fazer com que PDFs que não foram terminados de 
                #baixar sejam deletados
                try:
                    arq = open(os.path.join(self.pasta, "baixando"), "r")
                    nome2 = arq.read()
                    os.remove(nome2)
                    arq.close()
                    os.remove(os.path.join(self.pasta, "baixando"))
                except:
                    print "Erro remover nao terminado"
                    pass
                
                arq = open(os.path.join(self.pasta, "baixando"), "w")
                arq.write(nome)
                arq.close()
                
                self.baixar_pagina(num_secao, num_pagina, self.data, nome)
                
                os.remove(os.path.join(self.pasta, "baixando"))






class Diario_Oficial_do_MT(Diario_Justica_do_MT):

    nome = "Diario_Oficial_do_MT"
    numero_de_secoes = 1
    por_data = False

    # Baixa uma página de uma seção de uma data de jornal e coloca em uma pasta
    def baixar_pagina(self, num_secao, num_pagina, data, nome_arquivo):
        
        edicao = data
        
        pagina_jornal = "http://www.iomat.mt.gov.br/ler_pdf.php?download=ok&edi_id=" + str(edicao) + "&page=0"
            
        comando = ['wget', '-nc', '--output-document=' + nome_arquivo,
                    pagina_jornal]
        
        out, err = comandar(comando)

        if len(open(nome_arquivo).read()) < 100:
            try:
                os.remove(nome_arquivo)
            except:
                pass






class Diario_Oficial_Uniao(jornal):

    nome = "Diario_Oficial_Uniao"
    numero_de_secoes = 3

    # Baixa uma página de uma seção de uma data de jornal e coloca em uma pasta
    def baixar_pagina(self, num_secao, num_pagina, data, nome_arquivo):
        dados_jornal = "jornal=" + str(num_secao) + "&pagina=" + str(num_pagina)\
                        + "&data=" + data
    
        ## Essa é a página que deve ser baixada para conseguir os cookies
        ## para depois baixar o pdf desejado
        #pagina_referencia = \
        #    "http://www.in.gov.br/imprensa/visualiza/index.jsp?" + dados_jornal
        #
        #comando = ["wget", '--output-document='\
        #            + os.path.join(self.pasta, 'refer.html'), '--cookies=on',
        #            '--keep-session-cookies', '--save-cookies=cookies.txt',
        #            pagina_referencia]
        #
        ## Baixa a página para conseguir os cookies
        #comandar(comando)
        #
        #os.remove(os.path.join(self.pasta, 'refer.html'))
        
        # Essa é a página com o pdf desejado
        pagina_jornal = "http://pesquisa.in.gov.br/imprensa/servlet/INPDFViewer?"\
                        + dados_jornal + "&captchafield=firistAccess"
        
        #comando = ['wget', '-nc', '--output-document=' + nome_arquivo,
        #            '--referer="' + pagina_referencia, '--cookies=on',
        #            "--load-cookies=cookies.txt", "--keep-session-cookies",
        #            "--save-cookies=cookies.txt", pagina_jornal]

        comando = ['wget', '-nc', '--output-document=' + nome_arquivo,
                    pagina_jornal]
        
        # Baixa o PDF
        comandar(comando)
        
    def obter_num_paginas_secao(self, num_secao, data):
        dados_jornal = "jornal=" + str(num_secao) + "&pagina=1&data=" + data
        
        # Página que tem o número de páginas da seção
        pagina_referencia = \
            "http://pesquisa.in.gov.br/imprensa/jsp/visualiza/index.jsp?" + dados_jornal
        
        comando = ["wget", '--output-document='\
                + os.path.join(self.pasta, 'refer.html'), pagina_referencia]
        print comando
        
        # Baixa a página
        comandar(comando)
    
        arq = open(os.path.join(self.pasta, 'refer.html'))
        texto = arq.read()
        arq.close()
        os.remove(os.path.join(self.pasta, 'refer.html'))
        
        # Extrai do arquivo baixado a parte q fala sobre o número de páginas
        x1, x2, x3 = texto.partition("totalArquivos=")
        
        if x3:
            num_paginas_secao, x4, x5 = x3.partition('"')
        else:
            num_paginas_secao = 0
        
        return int(num_paginas_secao)
    
    
    
    

class Diario_da_Justica(jornal):

    nome = "Diario_da_Justiça"
    numero_de_secoes = 1

    # Baixa uma página de uma seção de uma data de jornal e coloca em uma pasta
    def baixar_pagina(self, num_secao, num_pagina, data, nome_arquivo):
        dados_jornal = "jornal=" + "126" + "&pagina=" + str(num_pagina)\
                        + "&data=" + data
    
        # Essa é a página que deve ser baixada para conseguir os cookies
        # para depois baixar o pdf desejado
        pagina_referencia = \
            "http://www.in.gov.br/imprensa/visualiza/index.jsp?" + dados_jornal
        
        comando = ["wget", '--output-document='\
                    + os.path.join(self.pasta, 'refer.html'), '--cookies=on',
                    '--keep-session-cookies', '--save-cookies=cookies.txt',
                    pagina_referencia]
        
        # Baixa a página para conseguir os cookies
        comandar(comando)
        
        os.remove(os.path.join(self.pasta, 'refer.html'))
        
        # Essa é a página com o pdf desejado
        pagina_jornal = "http://www.in.gov.br/imprensa/servlet/INPDFViewer?"\
                        + dados_jornal + "&captchafield=firistAccess"
        
        comando = ['wget', '-nc', '--output-document=' + nome_arquivo,
                    '--referer="' + pagina_referencia, '--cookies=on',
                    "--load-cookies=cookies.txt", "--keep-session-cookies",
                    "--save-cookies=cookies.txt", pagina_jornal]
        
        # Baixa o PDF
        comandar(comando)
        
    def obter_num_paginas_secao(self, num_secao, data):
        dados_jornal = "jornal=" + "126" + "&pagina=1&data=" + data
        
        # Página que tem o número de páginas da seção
        pagina_referencia = \
            "http://www.in.gov.br/imprensa/visualiza/index.jsp?" + dados_jornal
        
        comando = ["wget", '--output-document='\
                + os.path.join(self.pasta, 'refer.html'), pagina_referencia]
        
        # Baixa a página
        comandar(comando)
    
        arq = open(os.path.join(self.pasta, 'refer.html'))
        texto = arq.read()
        arq.close()
        os.remove(os.path.join(self.pasta, 'refer.html'))
        
        # Extrai do arquivo baixado a parte q fala sobre o número de páginas
        x1, x2, x3 = texto.partition("totalArquivos=")
        
        if x3:
            num_paginas_secao, x4, x5 = x3.partition('"')
        else:
            num_paginas_secao = 0
        
        return int(num_paginas_secao)
    
    
    
    

class Diario_TRF(jornal):

    nome = "Diario_TRF"
    numero_de_secoes = 1

    # Baixa uma página de uma seção de uma data de jornal e coloca em uma pasta
    def baixar_pagina(self, num_secao, num_pagina, data, nome_arquivo):
        dados_jornal = "jornal=" + "20" + "&pagina=" + str(num_pagina)\
                        + "&data=" + data
    
        # Essa é a página que deve ser baixada para conseguir os cookies
        # para depois baixar o pdf desejado
        pagina_referencia = \
            "http://www.in.gov.br/imprensa/visualiza/index.jsp?" + dados_jornal
        
        comando = ["wget", '--output-document='\
                    + os.path.join(self.pasta, 'refer.html'), '--cookies=on',
                    '--keep-session-cookies', '--save-cookies=cookies.txt',
                    pagina_referencia]
        
        # Baixa a página para conseguir os cookies
        comandar(comando)
        
        os.remove(os.path.join(self.pasta, 'refer.html'))
        
        # Essa é a página com o pdf desejado
        pagina_jornal = "http://www.in.gov.br/imprensa/servlet/INPDFViewer?"\
                        + dados_jornal + "&captchafield=firistAccess"
        
        comando = ['wget', '-nc', '--output-document=' + nome_arquivo,
                    '--referer="' + pagina_referencia, '--cookies=on',
                    "--load-cookies=cookies.txt", "--keep-session-cookies",
                    "--save-cookies=cookies.txt", pagina_jornal]
        
        # Baixa o PDF
        comandar(comando)
        
    def obter_num_paginas_secao(self, num_secao, data):
        dados_jornal = "jornal=" + "20" + "&pagina=1&data=" + data
        
        # Página que tem o número de páginas da seção
        pagina_referencia = \
            "http://www.in.gov.br/imprensa/visualiza/index.jsp?" + dados_jornal
        
        comando = ["wget", '--output-document='\
                + os.path.join(self.pasta, 'refer.html'), pagina_referencia]
        
        # Baixa a página
        comandar(comando)
    
        arq = open(os.path.join(self.pasta, 'refer.html'))
        texto = arq.read()
        arq.close()
        os.remove(os.path.join(self.pasta, 'refer.html'))
        
        # Extrai do arquivo baixado a parte q fala sobre o número de páginas
        x1, x2, x3 = texto.partition("totalArquivos=")
        
        if x3:
            num_paginas_secao, x4, x5 = x3.partition('"')
        else:
            num_paginas_secao = 0
        
        return int(num_paginas_secao)
    


    



class Diario_Oficial_SP(jornal):

    nome = "Diario_Oficial_SP"
    numero_de_secoes = 2
    
    secoes = ["exec1", "exec2"]
    meses = ["Janeiro", "Fevereiro", "Marco", "Abril", "Maio", "Junho", "Julho",
            "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

    # Baixa uma página de uma seção de uma data de jornal e coloca em uma pasta
    def baixar_pagina(self, num_secao, num_pagina, data, nome_arquivo):
        
        # Converte o número da seção para um dos nomes das seções
        secao = self.secoes[num_secao - 1]
        
        dia, mes, ano = data.split("/")
        mes = self.meses[int(mes) - 1]
        
        pagina_jornal = \
            'http://diariooficial.imprensaoficial.com.br/doflash/prototipo/'\
            + ano + '/' + mes + '/' + dia + '/' + secao + '/pdf/pg_'\
            + str(num_pagina).zfill(4) + '.pdf'
            
        comando = ['wget', '-nc', '--output-document=' + nome_arquivo,
                    pagina_jornal]
        
        comandar(comando)
        
    def obter_num_paginas_secao(self, num_secao, data):
        
        dia, mes, ano = data.split("/")
        pagina_referencia = \
            "http://diariooficial.imprensaoficial.com.br/nav_v4/header.asp?txtData="\
            + data + "&cad=" + str(num_secao + 3) + "&cedic=" + ano + mes + dia\
            + "&pg=1&acao=&edicao=&secao="
        
        comando = ['wget',
                '--output-document=' + os.path.join(self.pasta, 'refer.html'),
                pagina_referencia]
        comandar(comando)
        
        arq = open(os.path.join(self.pasta, 'refer.html'))
        texto = arq.read()
        arq.close()
        os.remove(os.path.join(self.pasta, 'refer.html'))
        
        x1, x2, x3 = texto.partition('<span class="tx_10 tx_bold">I de ')
        
        if x3:
            num_paginas_secao, x4, x5 = x3.partition('<')
        else:
            num_paginas_secao = -4        
        
        return int(num_paginas_secao) + 4
    

        






class monitor():

    def __init__(self, tipo, pasta):
        self.data_inicial = date_texto2(datetime.date.today())
        self.edicao_1 = 1
        self.edicao_2 = 1
        self.datas = {}
        self.tipo_jornal = tipo
        self.pasta = pasta
        self.achados = []
        self.complitude = 0
        
        # todos,achados,nenhum
        self.guardar = "todos"
        
        # Usado para parar durante uma atualização
        self.para = False
        
        try:
            os.mkdir(os.path.join(self.pasta, self.tipo_jornal.nome))
        except:
            pass
        
    def parar(self):
        self.para = True
        
    def salvar(self):
        arq = open(self.tipo_jornal.nome + ".dat", "w")
        pickle.dump(self, arq)
        
    def carregar(self):
        try:
            arq = open(self.tipo_jornal.nome + ".dat", "r")
            return pickle.load(arq)
        except:
            return self
        
    def calcular_complitude(self):
        um_dia = datetime.timedelta(days=1)
        dia = texto_date(self.data_inicial)
        amanha = datetime.date.today() + um_dia
        calculados = 0
        total = 0
        while dia < amanha:
            if self.datas.get(date_texto(dia)):
                calculados += 1
            dia += um_dia
            total += 1
        return float(calculados) / float(total)
    
    def reiniciar(self):
        self.achados = []
        self.datas = {}
        self.complitude = 0
        self.salvar()
    
    def alterar_data(self, data):
        self.data_inicial = data
        self.salvar()
        
    def alterar_edicao_1(self, ed):
        try:
            self.edicao_1 = int(ed)
        except:
            print "Erro int edicao", ed
            pass
        
    def alterar_edicao_2(self, ed):
        try:
            self.edicao_2 = int(ed)
        except:
            print "Erro int edicao", ed
            pass
        
    def alterar_guardar(self, tipo):
        self.guardar = tipo
        self.salvar()
        
    def retornar_achados(self):
        
        lista = []
        lista2 = []
        for linha in self.achados:
            data, dic = linha
            lista.append(data)
            for linha2 in dic:
                sec, pag = linha2
                lista.append("Seção: " + str(sec) + "  Página: " + str(pag))
                oco = dic[linha2]
                for linha3 in oco:
                    palavra, posicao = linha3
                    if palavra not in lista2:
                        lista2.append(palavra)
                ocors = ""
                for linha4 in lista2:
                    ocors += '"' + linha4 + '" '
                lista.append(ocors)
                
        return lista
    
    def atualizar(self, buscador):
        
        self.para = False
        
        if self.tipo_jornal.por_data:
            self.atualizar_por_data(buscador)
        else:
            self.atualizar_por_edicao(buscador)
            
    def atualizar_por_edicao(self, buscador):
        
        edicao_atual = self.edicao_1

        while edicao_atual <= self.edicao_2:
            
            if self.para:
                return None
            
            jornal_edicao = self.datas.get(edicao_atual)

            # Verifica se já não foi analisado o jornal da data
            if not jornal_edicao:
                
                documentar("Processando edicao: " + str(edicao_atual))
                
                diretorio = os.path.join(self.pasta, self.tipo_jornal.nome)
                
                try:
                    os.mkdir(diretorio)
                except:
                    pass
                j = self.tipo_jornal(edicao_atual, diretorio, self)
                print "Baixar!"
                ocorrencias = j.executar(buscador)
                
                if self.para:
                    return None
                
                if len(ocorrencias) != 0:
                    self.achados.append((edicao_atual, ocorrencias))
                        
                # Remove os arquivos e diretório caso o usuário queira,
                # ou caso aquele dia não teve jornal ( tamanho da primeira seção
                # provavelmente é 0 nesse caso )
                if (self.guardar == "nenhum") or (j.tam_secoes[0] == 0):
                    j.remover()
                    os.rmdir(diretorio)
                elif self.guardar == "achados":
                    if len(ocorrencias) == 0:
                        j.remover()
                        os.rmdir(diretorio)
                    else:
                        j.remover_pdfs_nao_usados()
                        j.remover_txts_nao_usados()
                    
                self.datas[edicao_atual] = "a"
                self.salvar()
                
            edicao_atual += 1
            
            print edicao_atual
            
        for l in self.retornar_achados():
            documentar(l)
            
            
    def atualizar_por_data(self, buscador):
        
        um_dia = datetime.timedelta(days=1)
        dia = texto_date(self.data_inicial)
        amanha = datetime.date.today() + um_dia

        while dia < amanha:
            
            if self.para:
                return None
            
            jornal_data = self.datas.get(date_texto(dia))

            # Verifica se já não foi analisado o jornal da data
            if not jornal_data:
                
                documentar("Processando dia: " + date_texto2(dia))
                
                diretorio = os.path.join(self.pasta, self.tipo_jornal.nome, \
                            date_texto(dia).replace("/", "_"))
                
                try:
                    os.mkdir(diretorio)
                except:
                    print "Erro dir monitor"
                    pass
                j = self.tipo_jornal(date_texto2(dia), diretorio, self)
                ocorrencias = j.executar(buscador)
                
                if self.para:
                    return None
                
                if len(ocorrencias) != 0:
                    self.achados.append((date_texto(dia), ocorrencias))
                        
                # Remove os arquivos e diretório caso o usuário queira,
                # ou caso aquele dia não teve jornal ( tamanho da primeira seção
                # provavelmente é 0 nesse caso )
                if (self.guardar == "nenhum") or (j.tam_secoes[0] == 0):
                    j.remover()
                    os.rmdir(diretorio)
                elif self.guardar == "achados":
                    if len(ocorrencias) == 0:
                        j.remover()
                        os.rmdir(diretorio)
                    else:
                        j.remover_pdfs_nao_usados()
                        j.remover_txts_nao_usados()
                    
                self.datas[date_texto(dia)] = "a"
                self.salvar()
                
            dia += um_dia
            
        for l in self.retornar_achados():
            documentar(l)











class gui():
    
    def __init__(self, buscadores, monitores):
        
        self.buscadores = buscadores
        self.monitores = monitores
        
        self.thread_atualizadora = None
        
        #Set the Glade file
        self.gladefile = "trazdia.glade"  
        self.wTree = gtk.glade.XML(self.gladefile) 
        
        #Create our dictionay and connect it
        dic = { 
                "on_alterar_data_clicked" : self.alterar_data,
                "on_alterar_data_ok_clicked" : self.alterar_data_ok,
                "on_alterar_data_cancelar_clicked" : self.alterar_data_cancelar,
                
                "on_alterar_palavras_ok_clicked" : self.alterar_palavras_ok,
                "on_alterar_palavras_cancelar_clicked" : self.alterar_palavras_cancelar,
                "on_alterar_palavras_busca_clicked" : self.alterar_palavras_busca,
                
                "on_lista_monitores_changed" : self.lista_monitores_alterada,
                
                "on_atualizar_clicked" : self.atualizar,
                "on_reiniciar_clicked" : self.reiniciar,
                
                "on_parar_clicked" : self.parar_atualizacao,
                
                "on_guardar_achados_clicked" : self.tipo_guardar,
                "on_guardar_nenhum_clicked" : self.tipo_guardar,
                "on_guardar_todos_clicked" : self.tipo_guardar,
                
                "on_ajuda_clicked" : self.mostrar_ajuda,
                "on_ajuda_ok_clicked" : self.ajuda_ok,
                
                "on_entrada_edicao_1_changed" : self.mudou_edicao_1,
                "on_entrada_edicao_2_changed" : self.mudou_edicao_2,
                
                "on_window1_destroy" : self.fechar,
                "on_sair_clicked" : self.fechar }
        
        self.wTree.signal_autoconnect(dic)
        
        self.janela_alterar_palavras = self.wTree.get_widget("janela_alterar_palavras")
        if (self.janela_alterar_palavras):
            self.janela_alterar_palavras.connect("destroy", self.janela_alterar_palavras.hide)
            
        self.janela_alterar_data = self.wTree.get_widget("janela_alterar_data")
        if (self.janela_alterar_data):
            self.janela_alterar_data.connect("destroy", self.janela_alterar_data.hide)
            
        self.janela_ajuda = self.wTree.get_widget("janela_ajuda")
        if (self.janela_ajuda):
            self.janela_ajuda.connect("destroy", self.janela_ajuda.hide)
            
        self.info_monitor = self.wTree.get_widget("info_monitor")
        self.data_inicial = self.wTree.get_widget("data_inicial")
        self.calendario = self.wTree.get_widget("calendario")
        
        self.guardar_todos = self.wTree.get_widget("guardar_todos")
        self.guardar_nenhum = self.wTree.get_widget("guardar_nenhum")
        self.guardar_achados = self.wTree.get_widget("guardar_achados")
        self.texto_ajuda = self.wTree.get_widget("texto_ajuda")
        self.log = self.wTree.get_widget("log")
        
        self.barra = self.wTree.get_widget("barra")
            
        self.palavras = self.wTree.get_widget("palavras")
        self.palavras_buffer = gtk.TextBuffer(None)
        self.palavras.set_buffer(self.palavras_buffer)
        
        self.caixa_data = self.wTree.get_widget("caixa_data")
        self.caixa_edicao = self.wTree.get_widget("caixa_edicao")
        
        self.entrada_edicao_1 = self.wTree.get_widget("entrada_edicao_1")
        self.entrada_edicao_2 = self.wTree.get_widget("entrada_edicao_2")
        
        a = ""
        for l in buscadores[0].palavras_procuradas:
            a += l + "\n"
        self.palavras_buffer.set_text(a)
        
        self.lista_monitores = self.wTree.get_widget("lista_monitores")
        store = gtk.ListStore(str)
        for m in self.monitores:
            store.append([m.tipo_jornal.nome])
        self.lista_monitores.set_model(store)
        cell = gtk.CellRendererText()
        self.lista_monitores.pack_start(cell, True)
        self.lista_monitores.add_attribute(cell, "text", 0)
        
        try:
            arq = open("Leiame.txt", "r")
            self.texto_ajuda.set_text(arq.read())
        except:
            print "Erro leiame"
            pass
        
        self.atualizador_barra = atualizador(self.atualiza_barra)
        self.atualizador_barra.start()
        
        self.atualizador_log = atualizador(self.atualiza_log)
        self.atualizador_log.start()
        
    def mudou_edicao_1(self, widget):
        self.monitores[self.num_monitor].alterar_edicao_1(widget.get_text())
        
    def mudou_edicao_2(self, widget):
        self.monitores[self.num_monitor].alterar_edicao_2(widget.get_text())
        
    def fechar(self, widget):
        for m in self.monitores:
            m.parar()
        
        self.atualizador_barra.parar()
        self.atualizador_log.parar()
        gtk.main_quit()
        
    def mostrar_ajuda(self, widget):
        self.janela_ajuda.show()
        
    def ajuda_ok(self, widget):
        self.janela_ajuda.hide()
        
    def parar_atualizacao(self, widget):
        self.monitores[self.num_monitor].parar()
    
    def alterar_palavras_ok(self, widget):
        self.janela_alterar_palavras.hide()
        com, fim = self.palavras_buffer.get_bounds()
        lista = self.palavras_buffer.get_text(com, fim).splitlines()
        self.buscadores[0].trocar(lista)
        self.buscadores[0].salvar()
        
    def alterar_palavras_cancelar(self, widget):
        self.janela_alterar_palavras.hide()
        
    def alterar_palavras_busca(self, widget):
        self.janela_alterar_palavras.show()
        
    def alterar_data(self, widget):
        self.janela_alterar_data.show()
        
    def alterar_data_cancelar(self, widget):
        self.janela_alterar_data.hide()
        
    def alterar_data_ok(self, widget):
        ano, mes, dia = self.calendario.get_date()
        data = str(dia).zfill(2) + "/" + str(mes + 1).zfill(2) + "/" + str(ano).zfill(4)
        self.monitores[self.num_monitor].alterar_data(data)
        data2 = self.monitores[self.num_monitor].data_inicial
        self.data_inicial.set_text(data2)
        self.janela_alterar_data.hide()
        
    def tipo_guardar(self, widget):
        if self.guardar_todos.get_active():
            self.monitores[self.num_monitor].alterar_guardar("todos")
        if self.guardar_nenhum.get_active():
            self.monitores[self.num_monitor].alterar_guardar("nenhum")
        if self.guardar_achados.get_active():
            self.monitores[self.num_monitor].alterar_guardar("achados")
        
    def lista_monitores_alterada(self, widget):
        self.num_monitor = self.lista_monitores.get_active()
        
        if self.monitores[self.num_monitor].tipo_jornal.por_data:
            self.caixa_edicao.hide()
            self.caixa_data.show()
            data = self.monitores[self.num_monitor].data_inicial
            self.data_inicial.set_text(data)
        else:
            ed1 = self.monitores[self.num_monitor].edicao_1
            ed2 = self.monitores[self.num_monitor].edicao_2
            self.entrada_edicao_1.set_text(str(ed1))
            self.entrada_edicao_2.set_text(str(ed2))
            self.caixa_edicao.show()
            self.caixa_data.hide()
            
        self.info_monitor.show()    
        
    def reiniciar(self, widget):
        self.monitores[self.num_monitor].reiniciar()
        
    def atualizar(self, widget):
        if (not self.thread_atualizadora) or \
        (self.thread_atualizadora.isAlive() == False):
            funcao = self.monitores[self.num_monitor].atualizar
            self.thread_atualizadora = \
                atualizador(funcao, uma_vez=True, arg=self.buscadores[0])
            self.thread_atualizadora.start()
        else:
            documentar("Processando outra coisa ainda...")
        
    def atualiza_barra(self):
        try:
            valor = self.monitores[self.num_monitor].calcular_complitude()
            gobject.idle_add(self.barra.set_fraction, valor)
        except:
            pass
            
    def atualiza_log(self):
        global LOGS
        texto = ""
        for linha in LOGS:
            texto += str(linha) + "\n"
        try:
            gobject.idle_add(self.log.set_text, texto)
        except:
            print "Erro log"
            pass
        
    
class atualizador(Thread):
    
    def __init__(self, funcao, intervalo=1, uma_vez=False, arg=None):
        Thread.__init__(self)
        self.flag = True
        self.funcao = funcao
        self.intervalo = intervalo
        self.uma_vez = uma_vez
        self.arg = arg
        
    def run(self):
        if self.uma_vez:
            if self.arg:
                self.funcao(self.arg)
            else:
                self.funcao()
        else:
            while self.flag:
                if self.arg:
                    self.funcao(self.arg)
                else:
                    self.funcao()
                    
                time.sleep(self.intervalo)
            
    def parar(self):
        self.flag = False
    






# Tenta criar uma pasta temporária
try:
    os.mkdir("jornais")
except:
    pass
    

if __name__ == "__main__":
    B = buscador("Oo")
    B.carregar()
    
    M = monitor(Diario_Oficial_Uniao, "jornais")
    M = M.carregar()
    
    M2 = monitor(Diario_Oficial_SP, "jornais")
    M2 = M2.carregar()
    
    M3 = monitor(Diario_da_Justica, "jornais")
    M3 = M3.carregar()
    
    M4 = monitor(Diario_TRF, "jornais")
    M4 = M4.carregar()
    
    M5 = monitor(Diario_Justica_do_MT, "jornais")
    M5 = M5.carregar()
    
    M6 = monitor(Diario_Oficial_do_MT, "jornais")
    M6 = M6.carregar()
    
    gobject.threads_init()
    # ADICIONAR NOVOS MONITORES AQUI TB!
    GUI = gui([B], [M, M2, M3, M4, M5, M6])
    gtk.main()
