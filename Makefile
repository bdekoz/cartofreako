CXX ?= g++
CPPFLAGS ?= -Isrc
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Wpedantic -Werror
TEST_OUTPUT ?= /tmp/cartofreako-tests

.PHONY: check
check:
	mkdir -p $(TEST_OUTPUT)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) src/test-cahill-keyes-projection.cc \
		-o $(TEST_OUTPUT)/test-cahill-keyes-projection
	$(TEST_OUTPUT)/test-cahill-keyes-projection
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) src/test-cahill-keyes-projection-api.cc \
		-o $(TEST_OUTPUT)/test-cahill-keyes-projection-api
	$(TEST_OUTPUT)/test-cahill-keyes-projection-api
