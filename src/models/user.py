from src.config.database import Database
import bcrypt

class User:
    @staticmethod
    def get_by_id(user_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("""
        SELECT id, email, name, lastname_paternal, lastname_maternal,
               avatar_url, bio, currently_working, working_hours_per_day,
               stress_frequency, points, language, theme, created_at
        FROM users 
        WHERE id = %s
    """, (user_id,))
            return cursor.fetchone()
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def update(user_id, data):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            fields = []
            values = []
            for key, value in data.items():
                if key == 'password':
                    hashed = bcrypt.hashpw(value.encode('utf-8'), bcrypt.gensalt())
                    fields.append("password_hash = %s")
                    values.append(hashed)
                elif key in ['name', 'lastname_paternal', 'email',
                             'lastname_maternal','avatar_url','bio',
                             'currently_working','working_hours_per_day',
                             'stress_frequency']:
                    fields.append(f"{key} = %s")
                    values.append(value)

            if not fields:
                return False

            query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
            values.append(user_id)
            cursor.execute(query, tuple(values))
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def delete(user_id):
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod  # ¡Este método debe estar DENTRO de la clase User!
    def verify_password(user_id, current_password):
        """Verifica si la contraseña actual coincide"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            if not user:
                return False
            
            # Asegúrate de que el hash sea tipo bytes
            stored_hash = user['password_hash'].encode('utf-8') if isinstance(user['password_hash'], str) else user['password_hash']
            return bcrypt.checkpw(
                current_password.encode('utf-8'),
                stored_hash
            )
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod  # ¡Este también debe estar DENTRO de la clase!
    def update_password(user_id, new_password):
        """Actualiza la contraseña en la base de datos"""
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (hashed_password, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            Database.close_connection(connection, cursor)



    @staticmethod
    def get_all_except(user_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name, avatar_url FROM users WHERE id != %s", (user_id,))
            return cursor.fetchall()
        finally:
            Database.close_connection(connection, cursor)
