import paramiko
import io
from sshtunnel import SSHTunnelForwarder
from sysclasses.clsDBA_ABS import clsDBA_ABS
from abc import ABC, abstractmethod

TYPE_MAPPING: dict[str, tuple[str, str]] | None = None

class clsDBA_SQL(clsDBA_ABS):
    def __init__(self, log):
        super().__init__(log)

        # Obligation de définir TYPE_MAPPING
        if self.TYPE_MAPPING is None:
            raise TypeError(f"{self.__class__   .__name__} must define TYPE_MAPPING class attribute")
        # Obligation de définir map_to_canonical
        if "map_to_canonical" not in self.__class__.__dict__:
            raise TypeError(
                f"{self.__name__} must implement map_to_canonical() method"
            )


    def connect_with_tunnel(self, db_params: dict, ssh_params: dict = None):
        host = db_params['host']
        port = db_params['port']

        if ssh_params and ssh_params.get('enabled'):
            try:
                self._log.info(f"Ouverture tunnel SSH vers {ssh_params['host']}...")
                
                # Lecture intègre (newline='') pour éviter la corruption Windows
                with open(ssh_params['key_path'], 'r', encoding='utf-8', newline='') as f:
                    key_text = f.read()
                
                key_stream = io.StringIO(key_text)
                mypkey = None

                # Support des formats Ed25519 et RSA (Paramiko 2.12)
                for key_class in [paramiko.Ed25519Key, paramiko.RSAKey, paramiko.ECDSAKey]:
                    try:
                        key_stream.seek(0)
                        mypkey = key_class.from_private_key(key_stream)
                        if mypkey: break
                    except Exception: continue

                if not mypkey:
                    raise ValueError("Clé privée non reconnue ou format invalide.")

                self._ssh_tunnel = SSHTunnelForwarder(
                    (ssh_params['host'], ssh_params['port']),
                    ssh_username=ssh_params['user'],
                    ssh_pkey=mypkey,
                    remote_bind_address=(host, port),
                    allow_agent=False
                )
                self._ssh_tunnel.start()
                
                host = '127.0.0.1'
                port = self._ssh_tunnel.local_bind_port
                self._log.info(f"Tunnel SSH établi sur le port local {port}")
                
            except Exception as e:
                self._log.error(f"Échec Tunnel SSH : {e}")
                raise

        # Appel de la méthode connect() de la classe fille (ex: Postgre)
        self.connect(host, port, db_params['dbname'], db_params['user'], db_params['pwd'])

    def execute_select(self, command: str, params: tuple = None, as_dict: bool = True):
        try:
            cursor = self._get_cursor()
            cursor.execute(command, params)
            if as_dict:
                columns = [col[0] for col in cursor.description]
                dataset = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                return dataset
            return cursor
        except Exception as e:
            self._log.error(f"SQL | Erreur Lecture : {e}")
            raise

    def execute_non_query(self, command: str, params: tuple = None):
        cursor = None
        try:
            cursor = self._get_cursor()
            cursor.execute(command, params)
            return cursor.rowcount
        except Exception as e:
            self._log.error(f"SQL | Erreur Action : {e}")
            raise
        finally:
            if cursor: cursor.close()

    def disconnect(self):
        if self._connection:
            self._connection.close()
            self._log.info("Connexion SQL fermée.")
        if self._ssh_tunnel:
            self._ssh_tunnel.stop()
            self._log.info("Tunnel SSH fermé.")
    
    @property
    @abstractmethod
    def placeholder(self) -> str:
        """Marqueur de paramètre SQL. '%s' pour psycopg2, '?' pour pyodbc."""
        pass

    @abstractmethod
    def map_to_canonical(self, *args, **kwargs) -> dict:
        pass

    def _get_type_mapping(self):
        if self.TYPE_MAPPING is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define TYPE_MAPPING"
            )
        return self.TYPE_MAPPING
    
    @abstractmethod
    def insert(self, schema, table, columns, values, returning_pk=None):
        raise NotImplementedError