import sqlite3
import SQLConnection as sqCon
import UserAOEW

class UserManager:
    _instance = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._instance.db_connection = sqCon.DatabaseConnection()
            cls.user_data = None
        return cls._instance

    def add_user(self, username, password):
        try:
            self.db_connection.execute_query(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            print(f"Utilisateur '{username}' ajouter.")
            return "Réussi"
        except sqlite3.IntegrityError:
            print(f"L'utilisateur '{username}' existe déjà.")
            return "Échec"

    def get_user(self, username, password):
        user_data = self.db_connection.fetch_one(
            "SELECT * FROM users WHERE username = ? and password = ?", (username,password,)
        )
        if user_data:
            print(f"Utilisateur trouvé: ID={user_data[0]}, Username='{user_data[1]}'")
            return True
        else:
            print(f"Utilisateur '{username}' n'existe pas.")
            return False

    def get_user_data(self, username):
        user_data = self.db_connection.fetch_one(
            "SELECT * FROM users WHERE username = ?", (username,)
        )
        if user_data:
            print(f"Utilisateur trouvé: ID={user_data[0]}, Username='{user_data[1]}'")
            return UserAOEW.UserAOEW(user_data[0],user_data[1],user_data[2])


    def delete_user(self, username):
        self.db_connection.execute_query(
            "DELETE FROM users WHERE username = ?", (username,)
        )
        print(f"L'utilisateur '{username}' est éffacé (S'il existe).")

    def list_all_users(self):
        users = self.db_connection.fetch_all("SELECT * FROM users")
        if users:
            print("All Users:")
            for user in users:
                print(f"  ID={user[0]}, Username='{user[1]}'")
        else:
            print("Aucun utilisateur trouvé.")