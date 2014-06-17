#!/usr/bin/env python
# -*- coding: utf8 -*-

#-------------------------------------------------------------------------------
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
#-------------------------------------------------------------------------------

from mechanize import Browser
import pickle
from datetime import date
import webbrowser

# Bibliotecas para a interface gráfica
try:
    import pygtk
    pygtk.require("2.0")
except:
    pass
try:
    import gtk
    import gtk.glade
    import gobject
except:
    sys.exit(1)


# Classe geral para ser usada por cada procurador de palavras
class Procurador():
    
    def __init__(self):
        self.num_anterior = 0
        self.num_antanterior = 0
        self.busca = ""
        
        hoje = date.today().strftime("%d/%m/%Y")  
        self.data_inicial = "01/01/"+hoje[-4:]
        self.data_final = hoje
    
    def alterar_busca(self,nova):
        self.busca = nova
    
    # Cada procurador de implementar essa função que retorna o número de itens
    # encontrados
    def num_itens(self,busca, data_inicial, data_final):
        pass
    
    def salvar(self):
        arq = open(self.nome + ".pro", "w")
        pickle.dump(self, arq)
    
    def carregar(self):
        try:
            arq = open(self.nome + ".pro", "r")
            return pickle.load(arq)
        except:
            return self
        
    # Retorna a página html com as buscas
    def retornar_html(self):
        return self.nome+".html"
    
    def atualizar(self):
        novos = self.num_itens(self.busca,self.data_inicial,self.data_final)
        self.num_antanterior = self.num_anterior
        if novos != self.num_anterior:
            self.num_anterior = novos
            self.salvar()
            return True
        else:
            return False
    

class DO_U(Procurador):

    nome = "Diario_Uniao"

    def num_itens(self,busca, data_inicial, data_final):
        br = Browser()
        response1 = \
            br.open("http://portal.in.gov.br/in/imprensa1/pesquisa_avancada")
        br.select_form(name="formBusca")
        br["texto_todas"] = busca
        br["dataPublicacaoInicial"] = data_inicial[:5]
        br["dataPublicacaoFinal"] = data_final[:5]
        br["ano"] = [data_final[-4:]]
        br["idJornal"] = ["1", "2", "3", "4"]
#        print(br.form)
        br.form.action = \
            "http://www.in.gov.br/imprensa/pesquisa/pesquisaresultado.jsp"
        res = br.submit()
        texto = res.read()
        x1, x2, x3 = texto.partition("ite")
        x1, x2, x3 = x1.rpartition(">")
        
        try:
            arq = open(self.retornar_html(),"w")
            arq.write(texto)
            arq.close()
        except:
            print("Erro ao tentar salvar página de buscas!")
        
        x3 = x3.replace(",","")
        x3 = x3.strip()
        #Retorna o número de itens achados
        if x3 == "Um":
            return 1
        
        if len(x3) > 0:
            return int(x3)
        else:
            return 0
        
        
class DO_SP(Procurador):

    nome = "Diario_SP"

    def num_itens(self,busca, data_inicial, data_final):
        
        try:
            br = Browser()
            
            self.endereco = 'http://www.imprensaoficial.com.br/PortalIO/DO/BuscaDO2001Resultado_11_3.aspx?f=xhitlist&xhitlist_sel=title%3bField%3adc%3atamanho%3bField%3adc%3adatapubl%3bField%3adc%3acaderno%3bitem-bookmark%3bhit-context&xhitlist_vpc=first&xhitlist_s=&xhitlist_q=('\
                        +busca+\
                        ')&filtrotodoscadernos=True&xhitlist_xsl=xhitlist.xsl&filtrocadernossalvar=todos%2cexeci%2cjucii%2casb%2cexecii%2cjudciii%2cjc%2ctrt2r%2cjudel%2cjudipi%2cjudipii%2ctrt15r%2cemp%2csup%2cdouj%2cdom%2ctjm%2ctre%2ctrt2aa%2cjfd%2coab&xhitlist_mh=9999&filtropalavraschave='\
                        +busca
                        
            response1 = br.open(self.endereco)
            
            texto = response1.read()
    
            x1, x2, x3 = texto.partition('<span id="lblDocumentosEncontrados" class="tx_red">')
            x3, x2, x1 = x3.partition("</span></td>")
                        
            x3 = x3.replace(",","")
            x3 = x3.strip()
            #Retorna o número de itens achados
            if x3 == "Um":
                return 1
        except:
            print("Erro no endereço!")
            print(self.endereco)
            x3 = "0"
        
        if len(x3) > 0:
            return int(x3)
        else:
            return 0
        
    def retornar_html(self):
        return self.endereco
    

class Gui():
    
    def __init__(self,procurador):
        
        self.procurador = procurador
        
        #Set the Glade file
        self.gladefile = "proc.glade"  
        self.wTree = gtk.glade.XML(self.gladefile) 
        
        self.janela_pal = self.wTree.get_widget("window3")
        
        #Create our dictionay and connect it
        dic = { 
               "on_window3_destroy" : lambda x:self.janela_pal.hide(),
               "on_pal_cancel_clicked" : lambda x:self.janela_pal.hide(),
               "on_pal_ok_clicked" : self.pal_ok, 
               
               "on_alt2_clicked" : self.pal_mostrar,
               "on_alt1_clicked" : self.pal_mostrar,
               
               "on_window1_destroy" : self.fechar,
               "on_window2_destroy" : self.fechar,
               "on_ok_clicked" : self.fechar,
                "on_botao_clicked" : self.fechar }
        
        self.wTree.signal_autoconnect(dic)
        
        self.texto = self.wTree.get_widget("texto")
        self.texto2 = self.wTree.get_widget("texto2")
        self.link = self.wTree.get_widget("link")
        self.pal = self.wTree.get_widget("pal")
        
        self.link.set_label("Mostrar Página")
        self.link.set_uri(self.procurador.retornar_html())
        
        novos = self.procurador.num_anterior - self.procurador.num_antanterior
        info = self.procurador.nome+"\n\n"\
                +"Agora: "+str(self.procurador.num_anterior)+" itens\n"\
                +"Antes: "+str(self.procurador.num_antanterior)+" itens"
                    
        self.texto.set_text(info+"\n\n"+str(novos)+" novo(s) itens achados!")
        
        self.texto2.set_text(info)
        
        self.janelaAchou = self.wTree.get_widget("window1")
        self.janelaNada = self.wTree.get_widget("window2")
        
        gtk.link_button_set_uri_hook(self.abrir_url)
        
    def fechar(self, widget):
        self.janelaAchou.hide()
        self.janelaNada.hide()
        gtk.main_quit()
    
    def abrir_url(self,widget,url):
        webbrowser.open(url)
        
    def trocar_janela(self):
        self.janelaAchou.hide()
        self.janelaNada.show()
        
    def pal_ok(self,widget):
        self.procurador.alterar_busca(self.pal.get_text())
        self.janela_pal.hide()
        
    def pal_mostrar(self,widget):
        self.pal.set_text(self.procurador.busca)
        self.janela_pal.show()
    
    
        
if __name__ == "__main__":
    
    # Nessa lista devem ficar todos os procuradores de palavras
    procuradores = [DO_U,DO_SP]
    
    for p in procuradores:
        proc = p().carregar()
        
        novos = proc.atualizar()
        
        gui = Gui(proc)
        if novos:
            gtk.main()
        else:
            gui.trocar_janela()
            gtk.main()
            
        proc.salvar()    