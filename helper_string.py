#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" helper_string.py """
""" Copyright 2018, Jogle Lew """

import json
import helper_const
import helper_global

lang_config = helper_const.LANG_LIST

for lang_code in lang_config:
    with open("i18n/%s.json" % lang_code, "r") as f:
        lang_dict = json.load(f)
    for item, value in lang_dict.items():
        helper_global.assign(item, value, lang=lang_code)
