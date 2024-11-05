#!/bin/bash

# Configurazione LDAP
LDAP_URL="ldap://localhost:10081"
BASE_DN="dc=myvd"
BIND_DN="cn=admin,dc=myvd"   # Modifica con il DN dell'amministratore
BIND_PW="your_password"      # Inserisci la password dell'amministratore
PAGE_SIZE=500                # Numero di entry per pagina

# File di esportazione
EXPORT_FILE_CIPGROUP="cipgroup.ldif"
EXPORT_FILE_USERS="users.ldif"

# Nuovo database (stesso server)
NEW_DB_URL="ldap://localhost:10081"

# Funzione per esportare con paginazione
export_with_pagination() {
    local base_dn=$1
    local export_file=$2
    local cookie=""
    > "$export_file"  # Cancella il file di export esistente

    while :; do
        # Esegue ldapsearch con paginazione
        ldapsearch -x -H "$LDAP_URL" -D "$BIND_DN" -w "$BIND_PW" -b "$base_dn" -E pr=$PAGE_SIZE/$cookie >> "$export_file"
        
        # Estrai il cookie per la prossima pagina
        cookie=$(grep -Po '(?<=\:: )\S+' "$export_file" | tail -1)
        
        # Se il cookie è vuoto, non ci sono altre pagine
        if [ -z "$cookie" ]; then
            break
        fi
    done
}

# Funzione per eliminare tutte le entries sotto una OU
delete_entries() {
    local base_dn=$1
    ldapsearch -x -H "$LDAP_URL" -D "$BIND_DN" -w "$BIND_PW" -b "$base_dn" dn | grep '^dn: ' | sed 's/^dn: //' | ldapdelete -x -H "$LDAP_URL" -D "$BIND_DN" -w "$BIND_PW"
}

# 1. Esporta le entries da "ou=cipgroup,dc=myvd" e "ou=users,dc=myvd" con paginazione
export_with_pagination "ou=cipgroup,$BASE_DN" "$EXPORT_FILE_CIPGROUP"
export_with_pagination "ou=users,$BASE_DN" "$EXPORT_FILE_USERS"

# 2. Elimina le entries attuali per partire da una situazione pulita
delete_entries "ou=cipgroup,$BASE_DN"
delete_entries "ou=users,$BASE_DN"

# 3. Importa le entries nel nuovo database
ldapadd -x -H "$NEW_DB_URL" -D "$BIND_DN" -w "$BIND_PW" -f "$EXPORT_FILE_CIPGROUP"
ldapadd -x -H "$NEW_DB_URL" -D "$BIND_DN" -w "$BIND_PW" -f "$EXPORT_FILE_USERS"

echo "Eliminazione e migrazione completate con successo."
