

#include <stdio.h>
#include <inttypes.h>

#include "jlink_api.h"

int main(void) {

  uint64_t rc = (uint64_t)JLINK_GetDLLVersion();
  printf("%lx", rc);

  //printf("%s\n", JLINK_GetDLLVersion());
  return 0;
}
