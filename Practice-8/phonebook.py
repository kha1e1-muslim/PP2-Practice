
import psycopg2
from connect import get_db_connection, close_db_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhoneBook:
    def __init__(self):
        self.conn = None
        
    def _get_cursor(self):
        """Get a database connection and cursor"""
        if not self.conn:
            self.conn = get_db_connection()
        return self.conn.cursor()
    
    def _close_connection(self):
        """Close the database connection"""
        if self.conn:
            close_db_connection(self.conn)
            self.conn = None
    
    def search_by_pattern(self, pattern):
        """Search contacts by pattern using the database function"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM search_contacts_by_pattern(%s)", (pattern,))
            results = cursor.fetchall()
            cursor.close()
            return results
        except psycopg2.Error as e:
            logger.error(f"Error searching contacts: {e}")
            self.conn.rollback()
            return []
    
    def upsert_contact(self, name, phone):
        """Insert or update a contact using the stored procedure"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("CALL upsert_contact(%s, %s)", (name, phone))
            self.conn.commit()
            cursor.close()
            logger.info(f"Contact {name} upserted successfully")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error upserting contact: {e}")
            self.conn.rollback()
            return False
    
    def bulk_insert_contacts(self, contacts):
        """
        Insert multiple contacts using the stored procedure
        contacts: list of tuples (name, phone)
        Returns: list of invalid contacts
        """
        try:
            cursor = self.conn.cursor()
            invalid_contacts = []
            
            for name, phone in contacts:
                cursor.execute("CALL insert_contact_if_valid(%s, %s)", (name, phone))

                cursor.execute("SELECT * FROM get_invalid_contacts()")
                invalid = cursor.fetchall()
                if invalid:
                    invalid_contacts.extend(invalid)
            
            self.conn.commit()
            cursor.close()
            logger.info(f"Bulk insert completed. {len(invalid_contacts)} invalid contacts found.")
            return invalid_contacts
        except psycopg2.Error as e:
            logger.error(f"Error in bulk insert: {e}")
            self.conn.rollback()
            return []
    
    def get_contacts_paginated(self, limit=10, offset=0):
        """Get contacts with pagination"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM get_contacts_paginated(%s, %s)", (limit, offset))
            results = cursor.fetchall()
            cursor.close()
            return results
        except psycopg2.Error as e:
            logger.error(f"Error getting paginated contacts: {e}")
            self.conn.rollback()
            return []
    
    def delete_contact(self, identifier):
        """
        Delete a contact by name or phone using stored procedure
        identifier: can be name or phone number
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("CALL delete_contact(%s)", (identifier,))
            self.conn.commit()
            cursor.close()
            logger.info(f"Contact with identifier '{identifier}' deleted successfully")
            return True
        except psycopg2.Error as e:
            logger.error(f"Error deleting contact: {e}")
            self.conn.rollback()
            return False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_connection()

def main():
    """Example usage of PhoneBook class"""
    phonebook = PhoneBook()
    phonebook._get_cursor()  

    print("Searching for 'john':")
    results = phonebook.search_by_pattern('john')
    for contact in results:
        print(contact)
    

    print("\nUpserting contact 'Jane Doe':")
    phonebook.upsert_contact('Jane Doe', '+1234567890')
    

    contacts_to_add = [
        ('Alice Smith', '+9876543210'),
        ('Bob Johnson', 'invalid_phone'),  
        ('Charlie Brown', '+5551234567')
    ]
    print("\nBulk inserting contacts:")
    invalid = phonebook.bulk_insert_contacts(contacts_to_add)
    print(f"Invalid contacts: {invalid}")
    print("\nFirst 5 contacts:")
    contacts = phonebook.get_contacts_paginated(5, 0)
    for contact in contacts:
        print(contact)
    

    print("\nDeleting contact 'Jane Doe':")
    phonebook.delete_contact('Jane Doe')
    
    phonebook._close_connection()

if __name__ == "__main__":
    main()