

#include <inttypes.h>
#include <stdio.h>

#include "jlink_api.h"

int main(void) {
  printf("JLINK_GetDLLVersion %d\n", JLINK_GetDLLVersion());
  printf("JLINKARM_GetDLLVersion %d\n", JLINKARM_GetDLLVersion());
  printf("JLINKARM_GetCompileDateTime %s\n", JLINKARM_GetCompileDateTime());
  return 0;
}
