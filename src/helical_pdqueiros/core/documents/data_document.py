import os
from dataclasses import dataclass, field
from pathlib import Path
import anndata as ad
from helical_pdqueiros.io.logger import logger
import uuid6
from typing import Iterable

@dataclass
class DataDocument():
    # I'm assuming that the client always provide the standard HDF5 file format
    data: ad.AnnData
    _id: str = field(default=None)
    s3_path: str = field(default=None)
    file_name: str = field(default=None)

    local_input_file_path: str = field(default=None)
    local_input_folder_path: str = field(default=None)
    local_output_file_path: str = field(default=None)
    local_output_folder_path: str = field(default=None)

    def __len__(self):
        return self.data.n_obs

    def __post_init__(self):
        if self.s3_path:
            path_object = Path(self.s3_path)
            self.file_name = f'{path_object.stem}__{self._id}.dataset' if self._id else f'{path_object.stem}.dataset'

        if self.s3_path or self.local_input_file_path or self.local_output_file_path:
            self.file_name = Path(self.s3_path or self.local_input_file_path or self.local_output_file_path).name

        if not self.local_input_folder_path and self.local_input_file_path:
            self.local_input_folder_path = Path(self.local_input_file_path).parent

        if not self.local_input_file_path and self.local_input_folder_path:
            self.local_input_file_path = os.path.join(self.local_input_folder_path, self.file_name)

        if not self.local_output_folder_path and self.local_output_file_path:
            self.local_output_folder_path = Path(self.local_output_file_path).parent

        if not self.local_output_file_path and self.local_output_folder_path:
            self.local_output_file_path = os.path.join(self.local_output_folder_path, self.file_name)

        logger.debug(f'Created {self}')

    def __iter__(self):
        try:
            for i in self.data:
                yield i
        except TypeError:
            return

    def save(self):
        if self.file_path:
            if not os.path.exists(self.file_path):
                self.data.write(self.file_path)
            else:
                logger.warning(f'File already exists, skipping overwrite: {self.file_path}')

    def yield_chunks(self, batch_size, load_to_memory: bool=False):
        for batch in self.batch_generator(self.data, batch_size=batch_size):
            if load_to_memory:
                batch.data.to_memory()
            yield batch

    @staticmethod
    def batch_generator(adata, batch_size):
        for i in range(0, len(adata), batch_size):
            batch = adata[i:i + batch_size, :]
            yield DataDocument(data=batch, _id=uuid6.uuid7().hex)


if __name__ == '__main__':
    from datasets import load_dataset
    from helical.utils import get_anndata_from_hf_dataset
    import anndata as ad
    from scipy.sparse import csr_matrix
    import numpy as np
    # hf_dataset = load_dataset("helical-ai/yolksac_human",split="train[:5%]", trust_remote_code=True, download_mode="reuse_cache_if_exists")
    # ann_data = get_anndata_from_hf_dataset(hf_dataset)
    # ann_data.write('/home/pedroq/workspace/helical_pdqueiros/data/dataset.h5ad')
    counts = csr_matrix(np.random.poisson(1, size=(5, 20)), dtype=np.float32)
    adata = ad.AnnData(counts)
    # print(type(ann_data), ann_data)
    print(dir(adata))
    document = DataDocument(adata)
    print(document)
    print(len(document))
    for i in document:
        print(dir(i))