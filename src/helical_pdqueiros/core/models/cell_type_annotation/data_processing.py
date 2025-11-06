from helical.models.base_models import HelicalRNAModel
from pathlib import Path
from anndata import AnnData
import anndata as ad
from helical.models.geneformer.geneformer_tokenizer import TranscriptomeTokenizer
from helical.models.geneformer.geneformer_config import GeneformerConfig
from helical.utils.mapping import map_gene_symbols_to_ensembl_ids
from datasets import Dataset
from typing import Optional
import os
from helical_pdqueiros.io.logger import logger
from helical_pdqueiros.core.documents.annotated_data import AnnotatedDataDocument
import ray

class CellTypeAnnotationDataProcessor(HelicalRNAModel):
    """
    This is a copy of the Geneformer, but I've decoupled the data processing from the model so that we can run it in a distributed environment without reloading the model per worker.
    """

    def __init__(self, configurer: GeneformerConfig) -> None:
        super().__init__()
        self.configurer = configurer
        self.config = configurer.config
        self.files_config = configurer.files_config
        self.tokenizer = TranscriptomeTokenizer(
            custom_attr_name_dict=self.config["custom_attr_name_dict"],
            nproc=self.config["nproc"],
            model_input_size=self.config["input_size"],
            special_token=self.config["special_token"],
            gene_median_file=self.files_config["gene_median_path"],
            token_dictionary_file=self.files_config["token_path"],
            gene_mapping_file=self.files_config["ensembl_dict_path"],
        )

    def get_embeddings(self):
        # TODO the get_embedding should not be an abstractmethod if we decouple it
        return

    def process_data(self,
                     adata: ad.AnnData,
                     gene_names: str = "index",
                     output_path: Optional[str] = None,
                     use_raw_counts: bool = True,
                     dataset_id: str = None,
                 ) -> Dataset:
        """
        Processes the data for the Geneformer model.

        Parameters
        ----------
        adata : AnnData
            The AnnData object containing the data to be processed. Geneformer uses Ensembl IDs to identify genes
            and currently supports only human genes. If the AnnData object already has an 'ensembl_id' column,
            the mapping step can be skipped.
        gene_names : str, optional, default="index"
            The column in `adata.var` that contains the gene names. If set to a value other than "ensembl_id",
            the gene symbols in that column will be mapped to Ensembl IDs using the 'pyensembl' package,
            which retrieves mappings from the Ensembl FTP server and loads them into a local database.
            - If set to "index", the index of the AnnData object will be used and mapped to Ensembl IDs.
            - If set to "ensembl_id", no mapping will occur.
            Special case:
                If the index of `adata` already contains Ensembl IDs, setting this to "index" will result in
                invalid mappings. In such cases, create a new column containing Ensembl IDs and pass "ensembl_id"
                as the value of `gene_names`.
        output_path : str, optional, default=None
            If specified, saves the tokenized dataset to the given output path.
        use_raw_counts : bool, optional, default=True
            Determines whether raw counts should be used.

        Returns
        -------
        Dataset
            The tokenized dataset in the form of a Huggingface Dataset object.
        """
        logger.debug(f"Processing data for Geneformer, dataset ID:{dataset_id}")
        self.ensure_rna_data_validity(adata, gene_names, use_raw_counts)
        # map gene symbols to ensemble ids if provided
        if gene_names != "ensembl_id":
            if (adata.var[gene_names].str.startswith("ENS").all()) or (
                adata.var[gene_names].str.startswith("None").any()
            ):
                message = (
                    "It seems an anndata with 'ensemble ids' and/or 'None' was passed. "
                    "Please set gene_names='ensembl_id' and remove 'None's to skip mapping."
                )
                logger.info(message)
                raise ValueError(message)
            adata = map_gene_symbols_to_ensembl_ids(adata, gene_names)

            if adata.var["ensembl_id"].isnull().all():
                message = "All gene symbols could not be mapped to Ensembl IDs. Please check the input data."
                logger.info(message)
                raise ValueError(message)

        tokenized_cells, cell_metadata = self.tokenizer.tokenize_anndata(adata)
        tokenized_dataset = self.tokenizer.create_dataset(tokenized_cells=tokenized_cells,
                                                          cell_metadata=cell_metadata,
                                                          use_generator=False)
        if output_path:
            path_object = Path(output_path)
            # these will be concatenated later ons
            dataset_name = f'{path_object.stem}__{dataset_id}.dataset' if dataset_id else f'{path_object.stem}.dataset'
            output_path = os.path.join(Path(output_path).parent, dataset_name)
            tokenized_dataset.save_to_disk(output_path)

        logger.info("Successfully processed the data for Geneformer.")
        return tokenized_dataset

@ray.remote
def ray_process_data(data_processor: CellTypeAnnotationDataProcessor, adata: ad.AnnData, dataset_id: str=None):
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