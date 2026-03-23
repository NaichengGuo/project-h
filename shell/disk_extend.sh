#磁盘扩容后不会立即生效 
sudo -i
lsblk
resize2fs /dev/nvme0n1p1
xfs_growfs -d /