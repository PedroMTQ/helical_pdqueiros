import anndata as ad
from helical.models.geneformer.geneformer_config import GeneformerConfig

import os
from helical_pdqueiros.core.documents.data_document import DataDocument
import ray
import logging
from helical_pdqueiros.io.logger import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

@ray.remote
def ray_process_data(data_processor: CellTypeAnnotationDataProcessor, adata: ad.AnnData, dataset_id: str=None):
    print('here')
    return data_processor.process_data(adata=adata, dataset_id=dataset_id)

def test_batched_data_processing():
    import anndata as ad
    from datasets import load_dataset
    import tempfile
    from helical.utils import get_anndata_from_hf_dataset
    hf_dataset = load_dataset("helical-ai/yolksac_human",split="train[:5%]", trust_remote_code=True, download_mode="reuse_cache_if_exists")
    ann_data = get_anndata_from_hf_dataset(hf_dataset)
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = os.path.join(temp_dir, 'dataset.h5ad')
        ann_data.write(file_path)
        ann_data = ad.read_h5ad(file_path)
        data_processor = CellTypeAnnotationDataProcessor(GeneformerConfig())
        document = AnnotatedDataDocument(ann_data)
        processed_data = []
        for batch in document.yield_batches(2):
            processed_data.append(ray_process_data.remote(data_processor=data_processor, adata=batch.data, dataset_id=batch._id))

            break
        processed_data = ray.get(processed_data)
        batched = processed_data[0][0:2]
        ann_data = ad.read_h5ad(file_path)
        document = AnnotatedDataDocument(ann_data)
        processed_data = data_processor.process_data(adata=document.data)
        full = processed_data[0:2]
        try:
            assert batched == full
            logger.info('Batch processing is working correctly')
        except AssertionError:
            logger.error('Batch processing is NOT working correctly')
        processed_data.append(data_processor.process_data(adata=batch.data.to_memory(),
                                                          dataset_id=batch._id))


if __name__ == '__main__':
    # test_batched_data_processing()
    import anndata as ad
    import h5py
    import ray
    ray.init()
    file_path = '/home/pedroq/workspace/helical_pdqueiros/data/dataset.h5ad'
    ann_data = ad.read_h5ad(file_path)
    data_processor = CellTypeAnnotationDataProcessor(GeneformerConfig())
    document = AnnotatedDataDocument(ann_data)
    processed_data = []
    for batch in document.yield_batches(2, load_to_memory=True):
        processed_data.append(ray_process_data.remote(data_processor=data_processor, adata=batch.data, dataset_id=batch._id))
        break
    print(processed_data)
    batched = ray.get(processed_data)
    batched = batched[0][0:2]
    print(batched)

    ann_data = ad.read_h5ad(file_path)
    document = AnnotatedDataDocument(ann_data)
    processed_data = data_processor.process_data(adata=document.data)
    full = processed_data[0:2]
    print('is batched data the same as full:', batched == full)


    # dataset = ray.data.from_items(document.yield_batches(2))
    # print('document.shape 1 ', document.shape)
    # processed_data = data_processor.process_data(document.data)
    # print('processed_data.shape', processed_data.shape)
    # print('document.shape 2', document.shape)
    # print('document.shape 3', document.data.shape)
    # print(processed_data)

    # ds = (document.document.map_batches(data_processor.process_data))