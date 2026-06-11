from __future__ import annotations
import io
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.filedatalake import DataLakeServiceClient
from app.settings import get_settings

class FabricOneLakeMaterialClient:
    """Read-only OneLake/Fabric adapter for material master/BOM/PPI extracts.

    Configure ONELAKE_ACCOUNT_URL, ONELAKE_FILE_SYSTEM, and ONELAKE_MATERIAL_PATH.
    Example account URL: https://onelake.dfs.fabric.microsoft.com
    """
    def __init__(self) -> None:
        s = get_settings()
        account_url = getattr(s, "onelake_account_url", None) or "https://onelake.dfs.fabric.microsoft.com"
        file_system = getattr(s, "onelake_file_system", None) or s.fabric_workspace_id
        if not (file_system and s.onelake_material_path):
            raise RuntimeError("FABRIC_WORKSPACE_ID/ONELAKE_FILE_SYSTEM and ONELAKE_MATERIAL_PATH are required")
        self.service = DataLakeServiceClient(account_url=account_url, credential=DefaultAzureCredential())
        self.file_system = file_system
        self.material_path = s.onelake_material_path

    def read_material_master(self) -> pd.DataFrame:
        fs = self.service.get_file_system_client(self.file_system)
        file_client = fs.get_file_client(self.material_path)
        data = file_client.download_file().readall()
        return pd.read_csv(io.BytesIO(data))
