import os
from dataclasses import dataclass, field
from pathlib import Path
import anndata as ad
from helical_pdqueiros.io.logger import logger
import uuid6

@dataclass
class DataDocument():
    file_path: str = field(default=None)
    _id: str = field(default=None)
    # I'm assuming that the client always provide the standard HDF5 file format
    data: ad.AnnData = field(default=None, repr=False)
    n_obs : int = field(default=None)
    n_vars : int = field(default=None)

    def __len__(self):
        return self.data.n_obs

    def __post_init__(self):
        if not self.data and not self.file_path:
            raise Exception(f'We need either data or file_path to create this {self.__class__.__name__} object')
        if not self.data:
            self.data = ad.read_h5ad(self.file_path)
        self.n_obs = self.data.n_obs
        self.n_vars = self.data.n_vars

    def __iter__(self):
        try:
            for i in self.data:
                yield i
        except TypeError:
            return

    def save(self, output_folder: str=None) -> str:
        if output_folder:
            file_path = os.path.join(output_folder, Path(self.file_path).name)
        else:
            file_path = self.file_path
        if not os.path.exists(file_path):
            self.data.write(file_path)
            return file_path
        else:
            logger.warning(f'File already exists, skipping overwrite: {file_path}')

    def yield_chunks(self, chunk_size: int, load_to_memory: bool=False):
        for i in range(0, len(self.data), chunk_size):
            chunk = self.data[i:i + chunk_size, :]
            if load_to_memory:
                chunk.data.to_memory()
            path_object = Path(self.file_path)
            file_parent_path = path_object.parent
            file_stem = path_object.stem
            file_extension = path_object.suffix
            chunk_id = uuid6.uuid7().hex
            chunk_file_name = f'{file_stem}__{chunk_id}{file_extension}'
            chunk_file_path = os.path.join(file_parent_path, chunk_file_name)
            chunk_document = DataDocument(data=chunk, file_path=chunk_file_path, _id=chunk_id)
            yield chunk_document
            break


if __name__ == '__main__':
    test_file = '/home/pedroq/workspace/helical_pdqueiros/tests/dataset.h5ad'
    document = DataDocument(file_path=test_file)
    for chunk in document.yield_chunks(chunk_size=2):
        print(chunk.file_path)
        break