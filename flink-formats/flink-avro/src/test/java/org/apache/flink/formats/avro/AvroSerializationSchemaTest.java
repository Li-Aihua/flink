/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements.  See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership.  The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License.  You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.apache.flink.formats.avro;

import org.apache.flink.api.common.serialization.SerializationSchema;
import org.apache.flink.formats.avro.generated.Address;
import org.apache.flink.formats.avro.utils.TestDataGenerator;

import org.apache.avro.generic.GenericRecord;
import org.junit.Test;

import java.util.Random;

import static org.apache.flink.formats.avro.utils.AvroTestUtils.writeRecord;
import static org.junit.Assert.assertArrayEquals;

/**
 * Tests for {@link AvroDeserializationSchema}.
 */
public class AvroSerializationSchemaTest {

	private static final Address address = TestDataGenerator.generateRandomAddress(new Random());

	@Test
	public void testGenericRecord() throws Exception {
		SerializationSchema<GenericRecord> deserializationSchema =
			AvroSerializationSchema.forGeneric(
				address.getSchema()
			);

		byte[] encodedAddress = writeRecord(address, Address.getClassSchema());
		byte[] dataSerialized = deserializationSchema.serialize(address);
		assertArrayEquals(encodedAddress, dataSerialized);
	}

	@Test
	public void testSpecificRecordWithConfluentSchemaRegistry() throws Exception {
		SerializationSchema<Address> deserializer = AvroSerializationSchema.forSpecific(Address.class);

		byte[] encodedAddress = writeRecord(address, Address.getClassSchema());
		byte[] serializedAddress = deserializer.serialize(address);
		assertArrayEquals(encodedAddress, serializedAddress);
	}
}
