# -*- coding: utf-8 -*-

from opinel.utils.console import printDebug, printError, printException
from opinel.utils.globals import manage_dictionary

from ScoutSuite.core.utils import recurse

class ProcessingEngine(object):
    """

    """

    def __init__(self, ruleset):
        # Organize rules by path
        self.ruleset = ruleset
        self.rules = {}
        for filename in self.ruleset.rules:
            for rule in self.ruleset.rules[filename]:
                if not rule.enabled:
                    continue
                try:
                    manage_dictionary(self.rules, rule.path, [])
                    self.rules[rule.path].append(rule)
                except Exception as e:
                    printError('Failed to create rule %s: %s' % (rule.path, e))


    def run(self, cloud_provider, skip_dashboard = False):
        # Clean up existing findings
        for service in cloud_provider.services:
            cloud_provider.services[service][self.ruleset.rule_type] = {}

        # Process each rule
        for finding_path in self.rules:
            for rule in self.rules[finding_path]:
                
                if not rule.enabled:  # or rule.service not in []: # TODO: handle this...
                    continue

                printDebug('Processing %s rule[%s]: "%s"' % (rule.service, rule.filename, rule.description))
                finding_path = rule.path
                path = finding_path.split('.')
                service = path[0]
                manage_dictionary(cloud_provider.services[service], self.ruleset.rule_type, {})
                cloud_provider.services[service][self.ruleset.rule_type][rule.key] = {}
                cloud_provider.services[service][self.ruleset.rule_type][rule.key]['description'] = rule.description
                cloud_provider.services[service][self.ruleset.rule_type][rule.key]['path'] = rule.path
                for attr in ['level', 'id_suffix', 'display_path']:
                    if hasattr(rule, attr):
                        cloud_provider.services[service][self.ruleset.rule_type][rule.key][attr] = getattr(rule, attr)
                try:
                    setattr(rule, 'checked_items', 0)
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['items'] = recurse(cloud_provider.services, cloud_provider.services, path, [], rule, True)
                    if skip_dashboard:
                        continue
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['dashboard_name'] = rule.dashboard_name
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['checked_items'] = rule.checked_items
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['flagged_items'] = len(cloud_provider.services[service][self.ruleset.rule_type][rule.key]['items'])
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['service'] = rule.service
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['rationale'] = rule.rationale if hasattr(rule, 'rationale') else 'No description available.'
                except Exception as e:
                    printException(e)
                    printError('Failed to process rule defined in %s' % rule.filename)
                    # Fallback if process rule failed to ensure report creation and data dump still happen
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['checked_items'] = 0
                    cloud_provider.services[service][self.ruleset.rule_type][rule.key]['flagged_items'] = 0

