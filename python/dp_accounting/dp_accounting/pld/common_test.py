# Copyright 2020 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import math
import unittest
from unittest import mock

from absl.testing import parameterized

from dp_accounting.pld import common
from dp_accounting.pld import test_util


class DifferentialPrivacyParametersTest(parameterized.TestCase):

  @parameterized.parameters((-0.1, 0.1), (1, -0.1), (1, 1.1))
  def test_epsilon_delta_value_errors(self, epsilon, delta):
    with self.assertRaises(ValueError):
      common.DifferentialPrivacyParameters(epsilon, delta)


class CommonTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'no_initial_guess',
          'func': (lambda x: -x),
          'value': -4.5,
          'lower_x': 0,
          'upper_x': 10,
          'initial_guess_x': None,
          'expected_x': 4.5,
          'increasing': False,
      }, {
          'testcase_name': 'with_initial_guess',
          'func': (lambda x: -x),
          'value': -5,
          'lower_x': 0,
          'upper_x': 10,
          'initial_guess_x': 2,
          'expected_x': 5,
          'increasing': False,
      }, {
          'testcase_name': 'out_of_range',
          'func': (lambda x: -x),
          'value': -5,
          'lower_x': 0,
          'upper_x': 4,
          'initial_guess_x': None,
          'expected_x': None,
          'increasing': False,
      }, {
          'testcase_name': 'infinite_upper_bound',
          'func': (lambda x: -1 / (1 / x)),
          'value': -5,
          'lower_x': 0,
          'upper_x': math.inf,
          'initial_guess_x': 2,
          'expected_x': 5,
          'increasing': False,
      }, {
          'testcase_name': 'increasing_no_initial_guess',
          'func': (lambda x: x**2),
          'value': 25,
          'lower_x': 0,
          'upper_x': 10,
          'initial_guess_x': None,
          'expected_x': 5,
          'increasing': True,
      }, {
          'testcase_name': 'increasing_with_initial_guess',
          'func': (lambda x: x**2),
          'value': 25,
          'lower_x': 0,
          'upper_x': 10,
          'initial_guess_x': 2,
          'expected_x': 5,
          'increasing': True,
      }, {
          'testcase_name': 'increasing_out_of_range',
          'func': (lambda x: x**2),
          'value': 5,
          'lower_x': 6,
          'upper_x': 10,
          'initial_guess_x': None,
          'expected_x': None,
          'increasing': True,
      }, {
          'testcase_name': 'discrete',
          'func': (lambda x: -x),
          'value': -4.5,
          'lower_x': 0,
          'upper_x': 10,
          'initial_guess_x': None,
          'expected_x': 5,
          'increasing': False,
          'discrete': True,
      })
  def test_inverse_monotone_function(self,
                                     func,
                                     value,
                                     lower_x,
                                     upper_x,
                                     initial_guess_x,
                                     expected_x,
                                     increasing,
                                     discrete=False):
    search_parameters = common.BinarySearchParameters(
        lower_x, upper_x, initial_guess=initial_guess_x, discrete=discrete)
    x = common.inverse_monotone_function(
        func, value, search_parameters, increasing=increasing)
    if expected_x is None:
      self.assertIsNone(x)
    else:
      self.assertAlmostEqual(expected_x, x)


class DictListConversionTest(parameterized.TestCase):

  @parameterized.named_parameters(
      {
          'testcase_name': 'truncate_both_sides',
          'input_list': [0.2, 0.5, 0.3],
          'offset': 1,
          'tail_mass_truncation': 0.6,
          'expected_result': {
              2: 0.5
          },
      }, {
          'testcase_name': 'truncate_lower_only',
          'input_list': [0.2, 0.5, 0.3],
          'offset': 1,
          'tail_mass_truncation': 0.4,
          'expected_result': {
              2: 0.5,
              3: 0.3
          },
      }, {
          'testcase_name': 'truncate_upper_only',
          'input_list': [0.4, 0.5, 0.1],
          'offset': 1,
          'tail_mass_truncation': 0.3,
          'expected_result': {
              1: 0.4,
              2: 0.5
          },
      }, {
          'testcase_name': 'truncate_all',
          'input_list': [0.4, 0.5, 0.1],
          'offset': 1,
          'tail_mass_truncation': 3,
          'expected_result': {},
      })
  def test_list_to_dict_truncation(self, input_list, offset,
                                   tail_mass_truncation, expected_result):
    result = common.list_to_dictionary(
        input_list, offset, tail_mass_truncation=tail_mass_truncation)
    test_util.assert_dictionary_almost_equal(self, expected_result, result)


class ConvolveTest(parameterized.TestCase):

  def test_convolve_dictionary(self):
    dictionary1 = {1: 2, 3: 4}
    dictionary2 = {2: 3, 4: 6}
    expected_result = {3: 6, 5: 24, 7: 24}
    result = common.convolve_dictionary(dictionary1, dictionary2)
    test_util.assert_dictionary_almost_equal(self, expected_result, result)

  def test_convolve_dictionary_with_truncation(self):
    dictionary1 = {1: 0.4, 2: 0.6}
    dictionary2 = {1: 0.7, 3: 0.3}
    expected_result = {3: 0.42, 4: 0.12}
    result = common.convolve_dictionary(dictionary1, dictionary2, 0.57)
    test_util.assert_dictionary_almost_equal(self, expected_result, result)

  def test_self_convolve_dictionary(self):
    inp_dictionary = {1: 2, 3: 5, 4: 6}
    expected_result = {
        3: 8,
        5: 60,
        6: 72,
        7: 150,
        8: 360,
        9: 341,
        10: 450,
        11: 540,
        12: 216
    }
    result = common.self_convolve_dictionary(inp_dictionary, 3)
    test_util.assert_dictionary_almost_equal(self, expected_result, result)

  @parameterized.parameters(([3, 5, 7], 2, [9, 30, 67, 70, 49]),
                            ([1, 3, 4], 3, [1, 9, 39, 99, 156, 144, 64]))
  def test_self_convolve_basic(self, input_list, num_times, expected_result):
    min_val, result_list = common.self_convolve(input_list, num_times)
    self.assertEqual(0, min_val)
    self.assertSequenceAlmostEqual(expected_result, result_list)

  @parameterized.parameters(([0.1, 0.4, 0.5], 3, [-1], 0.5, 2, 6),
                            ([0.2, 0.6, 0.2], 3, [1], 0.7, 0, 5))
  def test_compute_self_convolve_bounds(self, input_list, num_times, orders,
                                        tail_mass_truncation,
                                        expected_lower_bound,
                                        expected_upper_bound):
    lower_bound, upper_bound = common.compute_self_convolve_bounds(
        input_list, num_times, tail_mass_truncation, orders=orders)
    self.assertEqual(expected_lower_bound, lower_bound)
    self.assertEqual(expected_upper_bound, upper_bound)

  @parameterized.parameters(
      ([0.1, 0.4, 0.5], 3, 0.5, 2, [0.063, 0.184, 0.315, 0.301, 0.137]),
      ([0.2, 0.6, 0.2], 3, 0.7, 1, [0.08, 0.24, 0.36, 0.24, 0.08]))
  def test_compute_self_convolve_with_truncation(self, input_list, num_times,
                                                 tail_mass_truncation,
                                                 expected_min_val,
                                                 expected_result_list):
    min_val, result_list = common.self_convolve(
        input_list, num_times, tail_mass_truncation=tail_mass_truncation)
    self.assertEqual(min_val, expected_min_val)
    self.assertSequenceAlmostEqual(expected_result_list, result_list)

  @mock.patch.object(
      common, 'compute_self_convolve_bounds', return_value=(6, 6)
  )
  def test_compute_self_convolve_with_too_small_truncation(self, _):
    # When the truncation bounds returned from compute_self_convolve_bounds are
    # too small, the input should not be truncated.
    min_val, result_list = common.self_convolve([0, 0, 1], 3)
    self.assertEqual(min_val, 6)
    self.assertSequenceAlmostEqual([1], result_list)


class HelperMethodsTest(parameterized.TestCase):

  @parameterized.parameters(
      (5, 7, 3, 8.60998489),
      (0.5, 3, 0.1, 2.31676098),
      (10, 100000, 5, 100002.30258509))
  def test_log_a_times_exp_b_plus_c(self, a, b, c, expected_result):
    self.assertAlmostEqual(
        common.log_a_times_exp_b_plus_c(a, b, c), expected_result)

  def test_log_sinh_errors(self):
    with self.assertRaises(ValueError):
      common.log_sinh(-1)

  @parameterized.parameters(
      (0.0, 0.0),
      (1, math.log(math.sinh(1))),
      (100000, 100000 - math.log(2)),
  )
  def test_log_sinh(self, a, log_sinh_a):
    self.assertAlmostEqual(common.log_sinh(a), log_sinh_a)

  @parameterized.parameters(
      dict(a=1.0, b=0.0, asinh_exp_b_times_exp_a=0.0),
      dict(a=math.log(math.sinh(1)), b=1.0, asinh_exp_b_times_exp_a=1.0),
      dict(a=100000, b=0.5, asinh_exp_b_times_exp_a=100000),
      dict(a=math.log(math.sinh(1)), b=-1.0, asinh_exp_b_times_exp_a=-1.0),
      dict(a=100000, b=-0.5, asinh_exp_b_times_exp_a=-100000),
  )
  def test_asinh_exp(self, a, b, asinh_exp_b_times_exp_a):
    self.assertAlmostEqual(common.asinh_exp(a, b), asinh_exp_b_times_exp_a)

if __name__ == '__main__':
  unittest.main()
