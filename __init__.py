#
# Copyright (C) 2021, 2026 Bob Swift (rdswift)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, see <https://www.gnu.org/licenses/>.


from picard.plugin3.api import (
    Metadata,
    OptionsPage,
    PluginApi,
    t_,
)
from picard.tags import tag_names

from .ui_options_keep_only_tags import Ui_KeepOnlyTagsOptionsPage


USER_GUIDE_URL = 'https://picard-plugins-user-guides.readthedocs.io/en/latest/keep_only_tags/user_guide.html'

ALWAYS_KEEP_TAGS = {
    'album',
    'albumartist',
    'artist',
    'discnumber',
    'title',
    'totaldiscs',
    'totaltracks',
    'tracknumber',
}


class KeepOnlyTagsPlugin:
    def __init__(self, api: PluginApi):
        self.api = api

    def get_tag_lists(self) -> tuple[set, set]:
        """Get the lists of tags to keep.  This includes the tags specified in the plugin settings, the tags
        specified as preserved in the Tags options page, and the tags in 'ALWAYS_KEEP_TAGS'.

        Returns:
            tuple[set, set]: A set containing the tags to keep, and a set containing the wildcard tags to keep.
        """
        tag_set_1 = set()
        tag_set_2 = set()
        tag_list = str(self.api.plugin_config['keep_only_tags_list']).splitlines()
        for tag_name in [x.strip().lower() for x in tag_list]:
            if tag_name:
                star = tag_name.find('*')
                if star > 0:
                    tag_set_2.add(tag_name[:star])
                else:
                    tag_set_1.add(tag_name)
        if tag_set_1:
            tag_set_1.update(ALWAYS_KEEP_TAGS)
            preserved_tags = self.api.global_config.setting['preserved_tags']
            if preserved_tags:
                tag_set_1.update(x.lower() for x in preserved_tags)
        return tag_set_1, tag_set_2

    def update_tags(self, api, album, metadata, *args):
        verbose_log = self.api.plugin_config['verbose_log']
        tag_list_1, tag_list_2 = self.get_tag_lists()
        if tag_list_1 or tag_list_2:
            target = Metadata()
            target.copy(metadata)
            for (key, value) in target.rawitems():
                if not (key.startswith('~') or key.lower() in tag_list_1):
                    update = True
                    for test_key in tag_list_2:
                        if str(key).lower().startswith(test_key):
                            update = False
                            break
                    if update:
                        metadata['~ko_' + key] = metadata[key]
                        del metadata[key]
                        if verbose_log:
                            self.api.logger.debug("Replacing tag '%s' with variable '_ko_%s'", key, key)
        else:
            self.api.logger.error("Empty list of tags to keep. Processing aborted.")


class KeepOnlyTagsOptionsPage(OptionsPage):

    TITLE = t_("ui.title", "Keep Only Tags")
    HELP_URL = USER_GUIDE_URL

    def __init__(self, parent=None):
        super(KeepOnlyTagsOptionsPage, self).__init__(parent)
        self.ui = Ui_KeepOnlyTagsOptionsPage()
        self.ui.setupUi(self)

    def load(self):
        self.ui.cb_verbose_log.setChecked(self.api.plugin_config['verbose_log'])
        self.ui.tags_list_text.setPlainText(self.api.plugin_config['keep_only_tags_list'])

    def save(self):
        self.api.plugin_config['keep_only_tags_list'] = self.ui.tags_list_text.toPlainText()
        self.api.plugin_config['verbose_log'] = self.ui.cb_verbose_log.isChecked()

    def restore_defaults(self):
        super().restore_defaults()


def enable(api: PluginApi):
    """Called when plugin is enabled."""
    plugin = KeepOnlyTagsPlugin(api)

    TAGS_TO_STAR = ['performer']
    default_tags = '\n'.join(list(x + '*' if x in TAGS_TO_STAR else x for x in tag_names()))

    # Register configuration options
    api.plugin_config.register_option('verbose_log', False)
    api.plugin_config.register_option('keep_only_tags_list', default_tags)

    # Migrate settings from 2.x version if available
    migrate_settings(api)

    # Register options page
    api.register_options_page(KeepOnlyTagsOptionsPage)

    # Register the plugin to run at a HIGH priority so that it is working with
    # the original tags provided by MusicBrainz.
    api.register_album_metadata_processor(plugin.update_tags, priority=1000)
    api.register_track_metadata_processor(plugin.update_tags, priority=1000)


def migrate_settings(api: PluginApi):
    if api.global_config.setting.raw_value("keep_only_tags_list") is None:
        return

    api.logger.info("Migrating settings from 2.x version.")

    mapping = [
        ('keep_only_tags_list', str)
    ]

    for key, qtype in mapping:
        if api.global_config.setting.raw_value(key) is None:
            api.logger.debug("No old setting for key: '%s'", key,)
            continue
        api.plugin_config[key] = api.global_config.setting.raw_value(key, qtype=qtype)
        api.global_config.setting.remove(key)
