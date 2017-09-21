from __future__ import absolute_import

from sentry.integrations.example import ExampleSetupView
from sentry.integrations.helper import PipelineHelper
from sentry.models import Integration, OrganizationIntegration
from sentry.testutils import TestCase


class IntegrationSetupTest(TestCase):
    def setUp(self):
        super(IntegrationSetupTest, self).setUp()
        self.organization = self.create_organization(name='foo', owner=self.user)
        self.login_as(self.user)
        self.path = '/extensions/example/setup/'

    def test_basic_flow(self):
        # XXX(dcramer): a bit of a hackish way to initialize this
        request = self.make_request(self.user)
        PipelineHelper.initialize(
            request=request,
            organization=self.organization,
            provider_id='example',
            dialog=True,
        )
        self.save_session()

        with self.feature('organizations:integrations-v3'):
            resp = self.client.get(self.path)
            assert resp.status_code == 200
            assert ExampleSetupView.TEMPLATE in resp.content.decode('utf-8')

            resp = self.client.post(self.path, {'name': 'test'})
            assert resp.status_code == 200
            assert 'window.opener.postMessage(' in resp.content

        integration = Integration.objects.get(provider='example')
        assert integration.external_id == 'test'
        assert integration.name == 'test'
        assert integration.metadata == {}
        assert OrganizationIntegration.objects.filter(
            integration=integration,
            organization=self.organization,
        ).exists()
