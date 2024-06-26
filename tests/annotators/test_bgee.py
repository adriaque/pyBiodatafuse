#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for the Bgee annotator."""

import json
import os
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from pyBiodatafuse.annotators.bgee import get_gene_expression, get_version_bgee
from pyBiodatafuse.constants import BGEE


def test_sparql_get_version_bgee():
    """Test that the SPARQL endpoint returns the expected get_version_bgee results."""
    data_file_folder = os.path.join(os.path.dirname(__file__), "data")
    bgee_version_file_path = os.path.join(data_file_folder, "bgee_version_data.json")
    expected = pd.read_json(bgee_version_file_path)

    obtained_version = get_version_bgee()

    expected_version = {
        "source_version": expected["results"]["bindings"][0]["date_modified"]["value"]
    }

    assert obtained_version == expected_version


@patch("pyBiodatafuse.annotators.bgee.SPARQLWrapper.queryAndConvert")
def test_get_version_bgee(mock_sparql_request):
    """Test the get_version_bgee."""
    # TODO: need to find a fix for getting metadata from stable Bgee SPARQL endpoint
    data_file_folder = os.path.join(os.path.dirname(__file__), "data")
    bgee_version_file_path = os.path.join(data_file_folder, "bgee_version_data.json")

    mock_sparql_request.return_value = pd.read_json(bgee_version_file_path)

    obtained_version = get_version_bgee()

    expected_version = {
        "source_version": mock_sparql_request.return_value["results"]["bindings"][0][
            "date_modified"
        ]["value"]
    }

    assert obtained_version == expected_version


@patch("pyBiodatafuse.annotators.bgee.SPARQLWrapper.queryAndConvert")
def test_get_gene_expression(mock_sparql_request, bridgedb_dataframe):
    """Test the get_gene_expression function."""
    mock_data_list = []
    # we first use a "dummy" get version result to simulate the "api ready" call
    data_file_folder = os.path.join(os.path.dirname(__file__), "data")
    bgee_version_file_path = os.path.join(data_file_folder, "bgee_version_data.json")
    mock_version_data = pd.read_json(bgee_version_file_path)

    mock_data_list.append(mock_version_data)

    data_file_path = os.path.join(data_file_folder, "bgee_mock_data.json")

    with open(data_file_path) as f:
        mock_data = json.load(f)

    for json_response in mock_data:
        mock_data_list.append(pd.DataFrame.from_dict(json_response))

    bgee_version_file_path = os.path.join(data_file_folder, "bgee_version_data.json")
    mock_version_data = pd.read_json(bgee_version_file_path)

    mock_data_list.append(mock_version_data)

    mock_sparql_request.side_effect = mock_data_list

    obtained_data, metadata = get_gene_expression(bridgedb_dataframe)

    expected_data = pd.read_json(os.path.join(data_file_folder, "bgee_expected_data.json"))

    for index in range(len(expected_data[BGEE])):
        expected_expression_data = pd.DataFrame.from_dict(
            pd.json_normalize(expected_data[BGEE][index])
        )
        expected_expression_data = expected_expression_data.sort_values(
            by=["anatomical_entity_id", "expression_level", "developmental_stage_id"],
            ascending=False,
        )
        expected_expression_data = expected_expression_data.astype({"expression_level": float})
        expected_expression_data.reset_index(drop=True, inplace=True)

        obtained_expression_sorted = pd.DataFrame(
            pd.json_normalize(obtained_data[BGEE][index])
        ).sort_values(
            by=["anatomical_entity_id", "expression_level", "developmental_stage_id"],
            ascending=False,
        )
        obtained_expression_sorted = obtained_expression_sorted.astype({"expression_level": float})
        obtained_expression_sorted.reset_index(drop=True, inplace=True)
        assert_frame_equal(expected_expression_data, obtained_expression_sorted)

    assert True


@pytest.fixture(scope="module")
def bridgedb_dataframe():
    """Reusable sample Pandas DataFrame to be used as input for the tests."""
    return pd.DataFrame(
        {
            "identifier": ["AGRN", "ATXN7"],
            "identifier.source": ["HGNC", "HGNC"],
            "target": ["ENSG00000188157", "ENSG00000163635"],
            "target.source": ["Ensembl", "Ensembl"],
        }
    )
