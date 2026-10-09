import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import streamlit_shadcn_ui as ui
from streamlit.testing.v1 import AppTest
from season_data import COMPETITION_DATASETS, SEASON_YEARS, competition_summary, load_overview


APP_DIR = Path(__file__).resolve().parents[1]


class CompetitionSelectionTests(unittest.TestCase):
    def setUp(self):
        # Only the decorative animation request is mocked; CSV loading and
        # all chart rendering execute against the real local datasets.
        response = Mock(status_code=200)
        response.json.return_value = {
            'v': '5.7.4', 'fr': 30, 'ip': 0, 'op': 1,
            'w': 100, 'h': 100, 'layers': [],
        }
        self.animation = patch('requests.get', return_value=response)
        self.animation.start()
        self.addCleanup(self.animation.stop)
        self.addCleanup(lambda: plt.close('all'))
        self.app = AppTest.from_file(str(APP_DIR / 'app.py'), default_timeout=90)

    def run_app(self):
        plt.close('all')
        self.app.run()
        self.assertEqual([error.message for error in self.app.exception], [])

    def chart_specs(self):
        return [json.loads(chart.proto.figure.spec) for chart in self.app.get('plotly_chart')]

    def test_overview_switches_real_data_and_keeps_chart_layout(self):
        with patch.object(pd, 'read_csv', wraps=pd.read_csv) as csv_reads, \
                patch.object(ui, 'metric_card', wraps=ui.metric_card) as cards, \
                patch.object(st, 'pyplot', wraps=st.pyplot) as pyplot:
            self.run_app()
            self.assertEqual(self.app.selectbox(key='competition_year').value, 2025)
            cards.reset_mock()
            pyplot.reset_mock()
            self.app.selectbox(key='competition_year').select(2023)
            self.run_app()
            original_specs = self.chart_specs()
            self.assertEqual(len(original_specs), 6)
            self.assertEqual(pyplot.call_count, 2)
            self.assertEqual(cards.call_args_list[-1].kwargs['content'], '605')
            self.assertEqual([m.value for m in self.app.metric],
                             ['2.29', '27,223', '$74.75 million'])

            self.app.selectbox(key='competition_year').select(2025)
            self.run_app()
            new_specs = self.chart_specs()
            self.assertEqual(len(new_specs), 6)
            self.assertEqual(pyplot.call_count, 4)
            self.assertEqual(cards.call_args_list[-3].kwargs['content'], '24')
            self.assertEqual(cards.call_args_list[-2].kwargs['content'], '52')
            self.assertEqual(cards.call_args_list[-1].kwargs['content'], '543')
            self.assertEqual([m.value for m in self.app.metric],
                             ['2.33', '25,770', '$142.03 million'])
            self.assertEqual([m.delta for m in self.app.metric],
                             ['+0.04 from 2023', '-1,453 from 2023', '+ $67.28 million from 2023'])
            self.assertIn('estimated', self.app.metric[2].label)
            self.assertEqual(
                [s['layout']['title']['text'] for s in original_specs],
                [s['layout']['title']['text'] for s in new_specs],
            )
            uganda = [t for t in new_specs[0]['data'] if t['x'] == ['Uganda']]
            self.assertEqual([t['y'] for t in uganda], [[3], [7]])
            timing = new_specs[1]['data'][0]
            self.assertEqual(timing['type'], 'bar')
            self.assertEqual(timing['orientation'], 'h')
            self.assertEqual(timing['x'], [8, 21, 22, 21, 21, 24])
            self.assertEqual(timing['y'], ['0-15', '16-30', '31-45', '46-60', '61-75', '76-90'])
            self.assertEqual(timing['text'], ['6.8%', '17.9%', '18.8%', '17.9%', '17.9%', '20.5%'])
            self.assertEqual(timing['marker']['color'], ['#158106'] * 5 + ['#FC8600'])
            self.assertEqual(sum(new_specs[2]['data'][0]['values']), 121)
            self.assertEqual(len(self.app.caption), 0)
            self.assertTrue(all(isinstance(c.args[0], Path) for c in csv_reads.call_args_list))

            self.app.selectbox(key='competition_year').select(2023)
            self.run_app()
            self.assertEqual(self.chart_specs()[0]['data'], original_specs[0]['data'])
            self.assertEqual(self.chart_specs()[1]['data'], original_specs[1]['data'])
            self.assertEqual([m.value for m in self.app.metric],
                             ['2.29', '27,223', '$74.75 million'])
            self.assertEqual(len(self.app.caption), 0)

    def test_year_change_clears_incompatible_teams_and_comparisons(self):
        self.run_app()
        self.app.selectbox(key='competition_year').select(2023)
        self.app.radio[0].set_value('By Team')
        self.run_app()
        self.app.selectbox(key='selected_team').select('Guinea')
        self.run_app()
        self.app.multiselect(key='comparison_teams').set_value(['Ghana', 'Morocco'])
        self.run_app()

        self.app.selectbox(key='competition_year').select(2025)
        self.run_app()
        self.assertNotIn('Guinea', self.app.selectbox(key='selected_team').options)
        self.assertEqual(self.app.multiselect(key='comparison_teams').value, [])
        self.assertEqual(len(self.chart_specs()), 5)

        self.app.selectbox(key='selected_team').select('Uganda')
        self.run_app()
        self.app.multiselect(key='comparison_teams').set_value(['Benin', 'Morocco'])
        self.run_app()
        self.assertEqual(len(self.chart_specs()[-1]['data']), 3)
        self.app.selectbox(key='competition_year').select(2023)
        self.run_app()
        self.assertNotIn('Uganda', self.app.selectbox(key='selected_team').options)
        self.assertEqual(self.app.multiselect(key='comparison_teams').value, [])

    def test_all_2025_teams_render_existing_charts(self):
        self.run_app()
        self.app.selectbox(key='competition_year').select(2025)
        self.app.radio[0].set_value('By Team')
        self.run_app()
        teams = self.app.selectbox(key='selected_team').options
        self.assertEqual(len(teams), 24)
        for team in teams:
            with self.subTest(team=team):
                self.app.selectbox(key='selected_team').select(team)
                self.run_app()
                self.assertEqual(len(self.chart_specs()), 5)
                self.assertTrue(any(f'{team}</span> Stats' in m.value for m in self.app.markdown))

    def test_every_historical_overview_uses_its_own_data(self):
        self.run_app()
        expected_averages = {2010: '2.45', 2012: '2.38', 2013: '2.16', 2015: '2.13',
                             2017: '2.06', 2019: '1.96', 2021: '1.92'}
        self.assertEqual(self.app.selectbox(key='competition_year').options,
                         [str(year) for year in sorted(SEASON_YEARS, reverse=True)])
        for year in SEASON_YEARS[:-2]:
            with self.subTest(year=year):
                self.app.selectbox(key='competition_year').select(year)
                self.run_app()
                specs = self.chart_specs()
                self.assertEqual(len(specs), 6)
                squads = pd.read_csv(COMPETITION_DATASETS[year][0])
                self.assertEqual(len(specs[0]['data']), 2 * len(squads))
                summary, overview = competition_summary(year), load_overview(year)
                expected_attendance = ('N/A' if summary['attendance'] is None
                                       else f"{summary['attendance']:,.0f}")
                expected_revenue = ('N/A' if summary['revenue'] is None
                                    else f"${summary['revenue']:.2f} million")
                self.assertEqual([metric.value for metric in self.app.metric],
                                 [expected_averages[year], expected_attendance, expected_revenue])
                self.assertEqual(sum(specs[2]['data'][0]['values']),
                                 int(squads['Goals'].sum() + squads['Own Goals'].sum()))
                if overview.get('goal_timing'):
                    self.assertEqual(specs[1]['data'][0]['x'], overview['goal_timing']['goals'])
                else:
                    self.assertEqual(specs[1]['data'], [])
                    self.assertIn('unavailable', specs[1]['layout']['annotations'][0]['text'])
                for chart, field in [(3, 'Possession'), (4, 'Shots on Target %'), (5, 'Fouls Commited')]:
                    if squads[field].isna().all():
                        self.assertEqual(specs[chart]['data'], [])
                        self.assertIn('unavailable', specs[chart]['layout']['annotations'][0]['text'])
                self.assertEqual(len(self.app.caption), 0)

    def test_every_historical_team_and_comparison_renders(self):
        self.run_app()
        self.app.radio[0].set_value('By Team')
        for year in SEASON_YEARS[:-2]:
            self.app.selectbox(key='competition_year').select(year)
            self.run_app()
            self.assertEqual(self.app.multiselect(key='comparison_teams').value, [])
            teams = self.app.selectbox(key='selected_team').options
            for team in teams:
                with self.subTest(year=year, team=team):
                    self.app.selectbox(key='selected_team').select(team)
                    self.run_app()
                    specs = self.chart_specs()
                    self.assertEqual(len(specs), 5)
                    self.assertTrue(any(f'{team}</span> Stats' in value.value for value in self.app.markdown))
            comparison = [team for team in teams if team != self.app.selectbox(key='selected_team').value][:2]
            self.app.multiselect(key='comparison_teams').set_value(comparison)
            self.run_app()
            specs = self.chart_specs()
            if specs[-1]['data']:
                self.assertEqual(len(specs[-1]['data']), 3)
            else:
                self.assertIn('unavailable', specs[-1]['layout']['annotations'][0]['text'])


if __name__ == '__main__':
    unittest.main()
