locals {
  envs = { for tuple in regexall("(.*)=(.*)", file("${path.module}/../.env")) : tuple[0] => sensitive(tuple[1]) }
}
