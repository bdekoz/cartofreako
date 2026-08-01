CXX ?= g++
CPPFLAGS ?= -Isrc
CXXFLAGS ?= -std=c++20 -Wall -Wextra -Wpedantic -Werror
TEST_DIR := tests
TEST_BINARIES := \
	$(TEST_DIR)/test-cahill-keyes-projection \
	$(TEST_DIR)/test-cahill-keyes-projection-api

.PHONY: check clean
check:
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-cahill-keyes-projection.cc \
		-o $(TEST_DIR)/test-cahill-keyes-projection
	$(TEST_DIR)/test-cahill-keyes-projection
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) \
		$(TEST_DIR)/test-cahill-keyes-projection-api.cc \
		-o $(TEST_DIR)/test-cahill-keyes-projection-api
	$(TEST_DIR)/test-cahill-keyes-projection-api

clean:
	$(RM) $(TEST_BINARIES)
