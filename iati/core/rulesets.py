"""A module containg a core representation of IATI Rulesets.

Note:
    Rulesets are under-implemented since it is expected that their implementation will be similar to that of Codelists, which is currently unstable. Once Codelist stability has been increased, Rulesets may be fully-implemented.

Warning:
    The contents of this module have not been implemented. Their structure may change when they are implemented.

Todo:
    Implement Rulesets (and Rules). Likely worth completing the Codelist implementation first since the two will be similar.

"""
import json
import jsonschema
import re
import iati.core.default
import iati.core.utilities


_VALID_RULE_TYPES = ["no_more_than_one", "atleast_one", "dependent", "sum", "date_order", "regex_matches", "regex_no_matches", "startswith", "unique"]


def locate_constructor_for_rule_type(rule_type):
    """Locate the constructor for specific rule types.

    Args:
        rule_type (str): The name of the type of Rule to identify the class for.

    Returns:
        Rule implementation: A constructor for a class that inherits from Rule.

    Raises:
        KeyError: When a non-permitted `rule_type` is provided.

    Todo:
        Determine scope of this function, and how much testing is therefore required.

    """
    possible_rule_types = {
        'atleast_one': RuleAtLeastOne,
        'date_order': RuleDateOrder,
        'dependent': RuleDependent,
        'no_more_than_one': RuleNoMoreThanOne,
        'regex_matches': RuleRegexMatches,
        'regex_no_matches': RuleRegexNoMatches,
        'startswith': RuleStartsWith,
        'sum': RuleSum,
        'unique': RuleUnique
    }

    return possible_rule_types[rule_type]


class Ruleset(object):
    """Representation of a Ruleset as defined within the IATI SSOT.

    Warning:
        Rulesets have not yet been implemented. They will likely have a similar API to Codelists, although this is yet to be determined.

    """

    def __init__(self, ruleset_str):
        """Initialise a Ruleset.

        Args:
            ruleset_str (str): A string that represents a Ruleset.

        Raises:
            TypeError: When a ruleset_str is not a string.
            ValueError: When ruleset_str does not validate against the ruleset schema.

        Todo:
            May raise a UnicodeDecodeError or json.JSONDecodeError if passed a dodgey bytearray. Need to test.

        """
        self.ruleset = json.loads(ruleset_str, object_pairs_hook=iati.core.utilities.dict_raise_on_duplicates)
        self.validate_ruleset()
        self.rules = set()
        self.set_rules()

    def validate_ruleset(self):
        """Validate a Ruleset against the Ruleset Schema."""
        try:
            jsonschema.validate(self.ruleset, iati.core.default.ruleset_schema())
        except jsonschema.ValidationError:
            raise ValueError

    def set_rules(self):
        """Set the Rules of the Ruleset."""
        try:
            for xpath_base, rule in self.ruleset.items():
                for rule_type, cases in rule.items():
                    for case in cases['cases']:
                        constructor = locate_constructor_for_rule_type(rule_type)
                        new_rule = constructor(xpath_base, case)
                        self.rules.add(new_rule)
        except ValueError:
            raise


class Rule(object):
    """Representation of a Rule contained within a Ruleset.

    Acts as a base class for specific types of Rule that actually do something.

    Todo:
        Determine whether this should be an Abstract Base Class.

    """

    def __init__(self, xpath_base, case):
        """Initialise a Rule.

        Args:
            xpath_base (str): The base of the XPath that the Rule will act upon.
            case (dict): Specific configuration for this instance of the Rule.

        Raises:
            TypeError: When a parameter is of an incorrect type.
            ValueError: When a rule_type is not one of the permitted Rule types.

        """
        self.case = case
        self.xpath_base = xpath_base
        self._valid_rule_configuration(case)

    def _valid_rule_configuration(self, case):
        """Check that a configuration being passed into a Rule is valid for the given type of Rule.

        Note:
            The `name` attribute on the class must be set to a valid rule_type before this function is called.

        Args:
            case (dict): A dictionary of values, generally parsed as a case from a Ruleset.

        Raises:
            AttributeError: When the Rule's name is unset or not a permitted rule_type.
            ValueError: When the case is not valid for the type of Rule.

        """
        try:
            ruleset_schema_section = self._ruleset_schema_section()
        except AttributeError:
            raise

        try:
            jsonschema.validate(case, ruleset_schema_section)
        except jsonschema.ValidationError:
            raise ValueError

    def _ruleset_schema_section(self):
        """Locate the section of the Ruleset Schema relevant for the Rule.

        In doing so, makes required properties required.

        Returns:
            dict: A dictionary of the relevant part of the Ruleset Schema, based on the Rule's name.

        Raises:
            AttributeError: When the Rule's name is unset or not a permitted rule_type.

        """
        ruleset_schema = iati.core.default.ruleset_schema()
        partial_schema = ruleset_schema['patternProperties']['.+']['properties'][self.name]['properties']['cases']['items']  # pylint: disable=E1101
        partial_schema['required'] = [key for key in partial_schema['properties'].keys() if key != 'condition']

        return partial_schema

    def _extract_xpath_case(self, path):
        """Return full XPath from `xpath_base` and `path`."""
        full_path = self.xpath_base + '/' + path
        return full_path


class RuleNoMoreThanOne(Rule):
    """Representation of a Rule that checks that there is no more than one Element matching a given XPath.

    Warning:
        Rules have not yet been implemented. The structure of specific types of Rule will depend on how the base class is formed.

        The name of specific types of Rule may better indicate that they are Rules.

    """

    def __init__(self, xpath_base, case):
        """Initialise a `no_more_than_one` rule."""
        self.name = "no_more_than_one"

        super(RuleNoMoreThanOne, self).__init__(xpath_base, case)

    def is_valid_for(self, dataset_tree):
        """Check `dataset_tree` has no more than one instance of a given case for an Element.

        Args:
            dataset_tree: an etree created from an XML dataset.

        Returns:
            Boolean value that changes depending on whether one or fewer cases are found in the dataset_tree.

        """
        path = self.case['paths'][0]
        return len(dataset_tree.findall(self._extract_xpath_case(path))) <= 1


class RuleAtLeastOne(Rule):
    """Representation of a Rule that checks that there is at least one Element matching a given XPath.

    Warning:
        Rules have not yet been implemented. The structure of specific types of Rule will depend on how the base class is formed.

        The name of specific types of Rule may better indicate that they are Rules.

    """

    def __init__(self, xpath_base, case):
        """Initialise an `atleast_one` rule."""
        self.name = "atleast_one"

        super(RuleAtLeastOne, self).__init__(xpath_base, case)

    def is_valid_for(self, dataset_tree):
        """Check `dataset_tree` has at least one instance of a given case for an Element.

        Args:
            dataset_tree: an etree created from an XML dataset.

        Returns:
            Boolean value that changes depending on whether the case is found in the dataset_tree.

        """
        path = self.case['paths'][0]
        return dataset_tree.find(self._extract_xpath_case(path)) is not None


class RuleDateOrder(Rule):
    """A specific type of Rule.

    Todo:
        Add docstring

    """

    def __init__(self, xpath_base, case):
        """Initialise a `date_order` rule."""
        self.name = "date_order"

        super(RuleDateOrder, self).__init__(xpath_base, case)


class RuleDependent(Rule):
    """A specific type of Rule.

    Todo:
        Add docstring

    """

    def __init__(self, xpath_base, case):
        """Initialise a `dependent` rule."""
        self.name = "dependent"

        super(RuleDependent, self).__init__(xpath_base, case)


class RuleRegexMatches(Rule):
    """A specific type of Rule.

    Todo:
        Add docstring

    """

    def __init__(self, xpath_base, case):
        """Initialise a `regex_matches` rule."""
        self.name = "regex_matches"

        super(RuleRegexMatches, self).__init__(xpath_base, case)

    def is_valid_for(self, dataset_tree):
        """Check that the Element specified by `paths` matches the given regex case."""
        paths = self.case['paths']
        pattern = re.compile(self.case['regex'])

        for path in paths:
            results = dataset_tree.findall(self._extract_xpath_case(path))
            for result in results:
                return bool(pattern.match(result.text))


class RuleRegexNoMatches(Rule):
    """A specific type of Rule.

    Todo:
        Add docstring

    """

    def __init__(self, xpath_base, case):
        """Initialise a `regex_no_matches` rule."""
        self.name = "regex_no_matches"

        super(RuleRegexNoMatches, self).__init__(xpath_base, case)

    def is_valid_for(self, dataset_tree):
        """Rule implementation method."""
        # paths = self.case['paths']
        # pattern = re.compile(self.case['regex'])
        #
        # for path in paths:
        #     results = dataset_tree.findall(self._extract_xpath_case(path))
        #     for result in results:
        #         import pdb; pdb.set_trace()
        #         return not bool(pattern.match(result.text))
        return True


class RuleStartsWith(Rule):
    """A specific type of Rule.

    Todo:
        Add docstring

    """

    def __init__(self, xpath_base, case):
        """Initialise a `startswith` rule."""
        self.name = "startswith"

        super(RuleStartsWith, self).__init__(xpath_base, case)

    def is_valid_for(self):
        """Rule implementation method."""
        return True


class RuleSum(Rule):
    """A specific type of Rule.

    Todo:
        Add docstring

    """

    def __init__(self, xpath_base, case):
        """Initialise a `sum` rule."""
        self.name = "sum"

        super(RuleSum, self).__init__(xpath_base, case)

    def is_valid_for(self):
        """Rule implementation method."""
        return True


class RuleUnique(Rule):
    """A specific type of Rule.

    Todo:
        Add docstring

    """

    def __init__(self, xpath_base, case):
        """Initialise a `unique` rule."""
        self.name = "unique"

        super(RuleUnique, self).__init__(xpath_base, case)

    def is_valid_for(self):
        """Rule implementation method."""
        return True
