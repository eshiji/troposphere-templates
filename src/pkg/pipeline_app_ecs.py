# Third party imports
from troposphere import Template
# Local application imports
from common.parameters import add_parameters


def generate_template(d):

    # Set template metadata
    t = Template()
    t.add_version('2010-09-09')
    t.set_description(d['cf_template_description'])

    add_parameters(t, d)

    return t
