from database.distributore_DAO import DistributoreDAO
from model.distributore_DTO import Distributore

'''
    MODELLO:
    - Rappresenta la struttura dati
    - Si occupa di gestire lo stato dell'applicazione
    - Interagisce con il database
'''

class Model:
    def __init__(self):
        self._distributori = None
        self.load_distributori()

        self.__sequenza_ottima = []
        self.__costo_ottimo = -1

    def load_distributori(self):
        """ Carica tutti i distributori e li setta nella variabile self._distributori """
        self._distributori = DistributoreDAO.get_distributori()

    def get_prezzo_medio(self, mese:int):
        """
        Calcola, per ogni distributore, il prezzo medio al litro per il mese selezionato.
        :param mese: Mese selezionato (un intero da 1 a 12)
        :return: lista di tuple --> (nome del distributore, media), es. (Distributore A, 1.789)
        """
        lista_prezzi_medi = []  #lista dei risultati: una tupla (nome, media) per ogni distributore
        for distributore in self._distributori:  #scorro i distributori caricati all'avvio
            prezzi_mese = []  #lista dei prezzi del mese, riparte vuota per ogni distributore
            for prezzo in distributore.get_prezzi():  #ORM: chiedo i prezzi direttamente al distributore
                if prezzo.data.month == mese:  #tengo solo i prezzi del mese selezionato
                    prezzi_mese.append(prezzo.prezzo_litro)  #aggiungo solo il numero, non l'oggetto Prezzo
            media = sum(prezzi_mese) / len(prezzi_mese)  #calcolo la media dei prezzi del mese
            lista_prezzi_medi.append((distributore.nome, media))  #salvo la tupla (nome del distributore, media)
        return lista_prezzi_medi  #fuori dai cicli: restituisco i risultati di tutti i distributori

    def get_sequenza_ottima(self, mese:int):
        """
        Calcola la sequenza ottimale di rifornimenti nei primi 7 giorni
        :return: sequenza di nomi distributore ottimale
        :return: costo ottimale (cioè quello minimizzato dalla sequenza scelta)
        """
        self.__sequenza_ottima = []
        self.__costo_ottimo = -1
        prezzi_settimana = self.__get_prezzi_prima_settimana_mese(mese)

        self.__ricorsione([], 1, None, 0, prezzi_settimana)

        # Traduci gli ID in nomi
        id_to_nome = {distributore.id: distributore.nome for distributore in self._distributori}
        sequenza_nomi = [f"Giorno {giorno}: {id_to_nome[i]}" for giorno, i in enumerate(self.__sequenza_ottima, start=1)]
        return sequenza_nomi, round(self.__costo_ottimo, 2)

    def __ricorsione(self, sequenza_parziale, giorno, ultimo_distributore, costo_corrente, prezzi_settimana):
        """ Implementa la ricorsione """
        #condizione terminale: ho scelto un distributore per tutti i 7 giorni
        if giorno > 7:
            if costo_corrente < self.__costo_ottimo or self.__costo_ottimo == -1:  #è migliore della soluzione salvata, oppure è la prima (-1 = nessuna soluzione ancora)
                self.__costo_ottimo = costo_corrente  #salvo il nuovo costo minimo
                self.__sequenza_ottima = list(sequenza_parziale)  #salvo una copia, perché la lista verrà modificata dal backtracking
            return  #la ricorsione si ferma sempre al giorno 8, anche se la soluzione non è migliore

        for id_distributore, prezzi in prezzi_settimana.items():  #provo ogni distributore: ottengo il suo id e la lista dei suoi 7 prezzi
            #calcolo il costo della scelta di oggi
            costo_oggi = prezzi[giorno-1]*100  #prezzo di oggi (il giorno 1 sta all'indice 0) per 100 litri
            if ultimo_distributore is not None and ultimo_distributore != id_distributore:  #ieri ero da un distributore diverso (il giorno 1 non c'è un "ieri")
                costo_oggi += 5  #costo fisso dello spostamento
            nuovo_costo = costo_corrente + costo_oggi  #costo accumulato fino a oggi compreso
            sequenza_parziale.append(id_distributore)  #scelgo questo distributore per oggi
            self.__ricorsione(sequenza_parziale, giorno+1, id_distributore, nuovo_costo, prezzi_settimana)  #passo a domani: il distributore di oggi diventa "ieri"
            #backtracking
            sequenza_parziale.pop()  #annullo la scelta di oggi per provare l'altro distributore

    def __get_prezzi_prima_settimana_mese(self, mese: int):
        """
        Restituisce i prezzi dei primi 7 giorni del mese selezionato per ciascun distributore.
        :return: un dizionario: {id_distributore: [prezzo_giorno1, ..., prezzo_giorno7]}
        """
        prezzi_prima_settimana = {}  #dizionario dei risultati: {id_distributore: [7 prezzi]}
        for distributore in self._distributori:  #scorro i distributori caricati all'avvio
            lista_7_prezzi = []  #prezzi della prima settimana, riparte vuota per ogni distributore
            for prezzo in distributore.get_prezzi():  #chiedo i prezzi direttamente al distributore (ORM)
                if prezzo.data.month == mese and prezzo.data.day <= 7:  #tengo solo i giorni da 1 a 7 del mese selezionato
                    lista_7_prezzi.append(prezzo.prezzo_litro)  #aggiungo solo il prezzo al litro
            prezzi_prima_settimana[distributore.id] = lista_7_prezzi  #uso l'id come chiave: la ricorsione e id_to_nome lavorano con gli id
        return prezzi_prima_settimana  #restituisco il dizionario che userà la ricorsione