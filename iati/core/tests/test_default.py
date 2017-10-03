"""A module containing tests for the library representation of default values."""
import pytest
import iati.core.codelists
import iati.core.constants
import iati.core.default
import iati.core.schemas
import iati.core.tests.utilities


class TestDefault(object):
    """A container for tests relating to Default data."""

    @pytest.mark.parametrize("invalid_version", iati.core.tests.utilities.generate_test_types(['none'], True))
    @pytest.mark.parametrize("func_to_check", [
        iati.core.default.get_default_version_if_none,
        iati.core.default.codelists,
        iati.core.default.activity_schema,
        iati.core.default.organisation_schema
    ])
    def test_invalid_version(self, invalid_version, func_to_check):
        """Check that an invalid version causes an error when obtaining default data."""
        with pytest.raises(ValueError):
            func_to_check(invalid_version)


class TestDefaultCodelists(object):
    """A container for tests relating to default Codelists."""

    @pytest.fixture
    def codelist_name(self):
        """Return the name of a valid Codelist."""
        return 'Country'

    @pytest.mark.parametrize("invalid_version", iati.core.tests.utilities.generate_test_types(['none'], True))
    def test_invalid_version_single_codelist(self, invalid_version, codelist_name):
        """Check that an invalid version causes an error when obtaining a single default Codelist.

        Note:
            This is a separate test since the function takes a parameter other than the `version`.

        """
        with pytest.raises(ValueError):
            iati.core.default.codelist(codelist_name, invalid_version)

    def test_default_codelist_valid_at_all_versions(self, codelist_name, standard_version_optional):
        """Check that a named default Codelist may be located.

        Todo:
            Check internal values beyond the codelists being the correct type.
        """
        codelist = iati.core.default.codelist(codelist_name, *standard_version_optional)

        assert isinstance(codelist, iati.core.Codelist)
        assert codelist.name == codelist_name
        for code in codelist.codes:
            assert isinstance(code, iati.core.Code)

    @pytest.mark.parametrize("version, codelist_name, expected_type", [
        ('1.04', 'AidTypeFlag', iati.core.Codelist),
        ('1.05', 'AidTypeFlag', iati.core.Codelist),
        ('2.01', 'AidTypeFlag', ValueError),
        ('2.02', 'AidTypeFlag', ValueError),
        ('1.04', 'BudgetStatus', ValueError),
        ('1.05', 'BudgetStatus', ValueError),
        ('2.01', 'BudgetStatus', ValueError),
        ('2.02', 'BudgetStatus', iati.core.Codelist)
    ])
    def test_default_codelist_valid_only_at_some_versions(self, codelist_name, version, expected_type):
        """Check that a codelist that is valid at some version/s is not valid in other versions.

        Example:
            AidTypeFlag was an embedded codelist in v1.04 and v1.05, but is not valid at any version after this.
            For example, BudgetStatus was added as an embedded codelist in v2.02, so is not valid prior to this.
        """
        try:  # Note pytest.raises() is not used here in order to keep this test flexible for parameterization.
            result = iati.core.default.codelist(codelist_name, version)
        except ValueError as excinfo:
            result = excinfo

        assert isinstance(result, expected_type)

    @pytest.mark.parametrize("name", iati.core.tests.utilities.generate_test_types(['str'], True))
    def test_default_codelist_invalid_at_all_versions(self, name, standard_version_optional):
        """Check that trying to find a default Codelist with an invalid name raises an error."""
        with pytest.raises(ValueError) as excinfo:
            iati.core.default.codelist(name, *standard_version_optional)

        assert 'There is no default Codelist in version' in str(excinfo.value)

    def test_default_codelists_type(self, codelist_lengths_by_version):
        """Check that the default Codelists are of the correct type.

        Todo:
            Check internal values beyond the codelists being the correct type.
        """
        codelists = iati.core.default.codelists(codelist_lengths_by_version.version)

        assert isinstance(codelists, dict)
        assert len(codelists.values()) == codelist_lengths_by_version.expected_length
        for codelist in codelists.values():
            assert isinstance(codelist, iati.core.Codelist)

    def test_codelist_mapping_condition(self):
        """Check that the Codelist mapping file is having conditions read.

        Todo:
            Split into multiple tests.
        """
        mapping = iati.core.default.codelist_mapping()

        assert mapping['Sector'][0]['condition'] == "@vocabulary = '1' or not(@vocabulary)"
        assert mapping['Version'][0]['condition'] is None

    def test_codelist_mapping_xpath(self):
        """Check that the Codelist mapping file is being read for both org and activity mappings.

        Todo:
            Split into multiple tests.
        """
        mapping = iati.core.default.codelist_mapping()
        version_xpaths = [mapping['Version'][0]['xpath'], mapping['Version'][1]['xpath']]

        assert '//iati-activities/@version' in version_xpaths
        assert '//iati-organisations/@version' in version_xpaths
        assert len(mapping['InvalidCodelistName']) == 0

    def test_default_codelists_length(self, codelist_lengths_by_version):
        """Check that the default Codelists for each version contain the expected number of Codelists."""
        codelists = iati.core.default.codelists(codelist_lengths_by_version.version)

        assert len(codelists) == codelist_lengths_by_version.expected_length


class TestDefaultRulesets(object):
    """A container for tests relating to default Rulesets."""

    def test_default_ruleset(self, standard_version_optional):
        """Check that the default Ruleset is correct.

        Todo:
            Check internal values beyond the Ruleset being the correct type.

        """
        ruleset = iati.core.default.ruleset(*standard_version_optional)

        assert isinstance(ruleset, iati.core.Ruleset)

    def test_default_ruleset_validation_rules_valid(self, schema_ruleset):
        """Check that a fully valid IATI file does not raise any type of error (including rules/rulesets)."""
        data = iati.core.tests.utilities.load_as_dataset('valid_std_ruleset')
        result = iati.validator.full_validation(data, schema_ruleset)

        assert iati.validator.is_xml(data.xml_str)
        assert iati.validator.is_iati_xml(data, schema_ruleset)
        assert not result.contains_errors()

    @pytest.mark.parametrize("rule_error, invalid_dataset_name, info_text", [
        (
            'err-rule-at-least-one-conformance-fail',
            'invalid_std_ruleset_missing_sector_element',
            'At least one of `sector` or `transaction/sector` must be present within each `//iati-activity`.'
        ),
        (
            'err-rule-date-order-conformance-fail',
            'invalid_std_ruleset_bad_date_order',
            '`activity-date[@type=\'1\']/@iso-date` must be chronologically before `activity-date[@type=\'3\']/@iso-date` within each `//iati-activity`.'
        ),
        (
            'err-rule-regex-matches-conformance-fail',
            'invalid_std_ruleset_bad_identifier',
            'Each instance of `reporting-org/@ref` and `iati-identifier` and `participating-org/@ref` and `transaction/provider-org/@ref` and `transaction/receiver-org/@ref` within each `//iati-activity` must match the regular expression `[^\\/\\&\\|\\?]+`.'  # noqa: disable=E501 # pylint: disable=line-too-long
        ),
        (
            'err-rule-sum-conformance-fail',
            'invalid_std_ruleset_does_not_sum_100',
            'Within each `//iati-activity`, the sum of values matched at `recipient-country/@percentage` and `recipient-region/@percentage` must be `100`.'
        )
        # Note the Rules relating to 'dependent', 'no_more_than_one', 'regex_no_matches', 'startswith' and 'unique' are not used in the Standard Ruleset.
    ])
    def test_default_ruleset_validation_rules_invalid(self, schema_ruleset, rule_error, invalid_dataset_name, info_text):
        """Check that the expected rule error is detected when validating files containing invalid data for that rule.

        Note:
            The fixed strings being checked here may be a tad annoying to maintain.
            `test_rule_string_output_general` and `test_rule_string_output_specific` in `test_rulesets.py` do something related for Rules. As such, something more generic may work better in the future.

        Todo:
            Consider whether this test should remove all warnings and assert that there is only the expected warning contained within the test file.

            Check that the expected missing elements appear the the help text for the given element.

        """
        data = iati.core.tests.utilities.load_as_dataset(invalid_dataset_name)
        result = iati.validator.full_validation(data, schema_ruleset)
        errors_for_rule_error = result.get_errors_or_warnings_by_name(rule_error)
        errors_for_ruleset = result.get_errors_or_warnings_by_name('err-ruleset-conformance-fail')

        assert iati.validator.is_xml(data.xml_str)
        assert iati.validator.is_iati_xml(data, schema_ruleset)
        assert not iati.validator.is_valid(data, schema_ruleset)
        assert len(errors_for_rule_error) == 1
        assert len(errors_for_ruleset) == 1
        assert info_text in errors_for_rule_error[0].info


class TestDefaultSchemas(object):
    """A container for tests relating to default Schemas."""

    def test_default_activity_schemas(self, standard_version_optional):
        """Check that the default ActivitySchemas are correct.

        Todo:
            Check internal values beyond the schemas being the correct type.
        """
        schema = iati.core.default.activity_schema(*standard_version_optional)

        assert isinstance(schema, iati.core.ActivitySchema)

    def test_default_organisation_schemas(self, standard_version_optional):
        """Check that the default ActivitySchemas are correct.

        Todo:
            Check internal values beyond the schemas being the correct type.
        """
        schema = iati.core.default.organisation_schema(*standard_version_optional)

        assert isinstance(schema, iati.core.OrganisationSchema)

    @pytest.mark.parametrize("population_status", [[], [True]])
    @pytest.mark.parametrize("schema_func", [
        iati.core.default.activity_schema,
        iati.core.default.organisation_schema
    ])
    def test_default_schemas_populated(self, population_status, schema_func, codelist_lengths_by_version):
        """Check that the default Codelists for each version contain the expected number of Codelists."""
        schema = schema_func(codelist_lengths_by_version.version, *population_status)

        assert len(schema.codelists) == codelist_lengths_by_version.expected_length
        assert len(schema.rulesets) == 1

    @pytest.mark.parametrize("schema_func", [
        iati.core.default.activity_schema,
        iati.core.default.organisation_schema
    ])
    def test_default_schemas_unpopulated(self, schema_func, standard_version_mandatory):
        """Check that the default Codelists for each version contain the expected number of Codelists."""
        schema = schema_func(standard_version_mandatory[0], False)

        assert schema.codelists == set()
        assert schema.rulesets == set()


class TestDefaultModifications(object):
    """A container for tests relating to the ability to modify defaults."""

    @pytest.fixture
    def codelist_name(self):
        """Return the name of a Codelist that exists at all versions of the Standard."""
        return 'Country'

    @pytest.fixture
    def codelist(self, codelist_name):
        """Return a default Codelist that is part of the IATI Standard."""
        return iati.core.default.codelist(codelist_name)

    @pytest.fixture
    def codelist_non_default(self):
        """Return a Codelist that is not part of the IATI Standard."""
        return iati.core.Codelist('custom codelist')

    @pytest.fixture
    def new_code(self):
        """Return a Code object that has not been added to a Codelist."""
        return iati.core.Code('new code value', 'new code name')

    def test_default_codelist_modification(self, codelist_name, new_code, standard_version_optional):
        """Check that a default Codelist cannot be modified by adding Codes to returned lists."""
        default_codelist = iati.core.default.codelist(codelist_name, *standard_version_optional)
        base_default_codelist_length = len(default_codelist.codes)

        default_codelist.codes.add(new_code)
        unmodified_codelist = iati.core.default.codelist(codelist_name, *standard_version_optional)

        assert len(default_codelist.codes) == base_default_codelist_length + 1
        assert len(unmodified_codelist.codes) == base_default_codelist_length

    def test_default_codelists_modification(self, codelist_name, new_code, standard_version_optional):
        """Check that default Codelists cannot be modified by adding Codes to returned lists with default parameters."""
        default_codelists = iati.core.default.codelists(*standard_version_optional)
        codelist_of_interest = default_codelists[codelist_name]
        base_default_codelist_length = len(codelist_of_interest.codes)

        codelist_of_interest.codes.add(new_code)
        unmodified_codelists = iati.core.default.codelists(*standard_version_optional)
        unmodified_codelist_of_interest = unmodified_codelists[codelist_name]

        assert len(codelist_of_interest.codes) == base_default_codelist_length + 1
        assert len(unmodified_codelist_of_interest.codes) == base_default_codelist_length

    @pytest.mark.parametrize("default_call", [
        iati.core.default.activity_schema,
        iati.core.default.organisation_schema
    ])
    def test_default_x_schema_modification_unpopulated(self, default_call, codelist, standard_version_mandatory):
        """Check that unpopulated default Schemas cannot be modified.

        Note:
            Implementation is by attempting to add a Codelist to the Schema.

        """
        default_schema = default_call(standard_version_mandatory[0], False)
        base_codelist_count = len(default_schema.codelists)

        default_schema.codelists.add(codelist)
        unmodified_schema = default_call(standard_version_mandatory[0], False)

        assert len(default_schema.codelists) == base_codelist_count + 1
        assert len(unmodified_schema.codelists) == base_codelist_count

    @pytest.mark.parametrize("default_call", [
        iati.core.default.activity_schema,
        iati.core.default.organisation_schema
    ])
    def test_default_x_schema_modification_populated(self, default_call, codelist_non_default, standard_version_mandatory):
        """Check that populated default Schemas cannot be modified.

        Note:
            Implementation is by attempting to add a Codelist to the Schema.

        """
        default_schema = default_call(standard_version_mandatory[0], True)
        base_codelist_count = len(default_schema.codelists)

        default_schema.codelists.add(codelist_non_default)
        unmodified_schema = default_call(standard_version_mandatory[0], True)

        assert len(default_schema.codelists) == base_codelist_count + 1
        assert len(unmodified_schema.codelists) == base_codelist_count
