
tar -zxvf JLink_Linux_V510p_x86_64.tgz

cp ./JLink_Linux_V510p_x86_64/libjlinkarm.so.5.10.16 .

ln -sf ./libjlinkarm.so.5.10.16 ~/work/pycs/lib64/libjlinkarm.so
ln -sf ./libjlinkarm.so.5.10.16 ~/work/pycs/lib64/libjlinkarm.so.5

Gives:

libjlinkarm.so -> ./libjlinkarm.so.5.10.16
libjlinkarm.so.5 -> ./libjlinkarm.so.5.10.16
libjlinkarm.so.5.10.16
