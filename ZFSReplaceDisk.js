Ext.define('Proxmox.window.ZFSReplaceDisk', {
    extend: 'Proxmox.window.Edit',
    alias: 'widget.pmxZFSReplaceDisk',
    mixins: ['Proxmox.Mixin.CBind'],

    showProgress: true,
    isCreate: true,
    submitText: gettext('Replace'),
    width: 450,

    cbindData: function (initialConfig) {
        let me = this;
        return {
            title: `${gettext('Replace Disk')}: ${me.olddevice}`,
            url: `/nodes/${me.nodename}/disks/zfs/${encodeURIComponent(me.zpool)}/replace`,
        };
    },

    method: 'POST',

    cbind: {
        title: '{title}',
        url: '{url}',
    },

    extraRequestParams: {},

    initComponent: function () {
        let me = this;

        if (!me.nodename) {
            throw 'no node name specified';
        }
        if (!me.zpool) {
            throw 'no zpool specified';
        }
        if (!me.olddevice) {
            throw 'no old device specified';
        }

        me.extraRequestParams = { 'old-device': me.olddevice };

        me.callParent();
    },

    items: [
        {
            xtype: 'displayfield',
            fieldLabel: gettext('Pool'),
            cbind: {
                value: '{zpool}',
            },
        },
        {
            xtype: 'displayfield',
            fieldLabel: gettext('Old Device'),
            cbind: {
                value: '{olddevice}',
            },
        },
        {
            xtype: 'pmxDiskSelector',
            name: 'new-device',
            fieldLabel: gettext('New Device'),
            diskType: 'unused',
            allowBlank: false,
            cbind: {
                nodename: '{nodename}',
            },
        },
    ],
});
