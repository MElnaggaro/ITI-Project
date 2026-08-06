BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0001_initial_schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE tenants (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    code VARCHAR(100) NOT NULL, 
    status VARCHAR(30) DEFAULT 'active' NOT NULL, 
    settings JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_tenants PRIMARY KEY (id), 
    CONSTRAINT uq_tenants_code UNIQUE (code)
);

CREATE TABLE users (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    email VARCHAR(255) NOT NULL, 
    full_name VARCHAR(255), 
    password_hash TEXT, 
    status VARCHAR(30) DEFAULT 'active' NOT NULL, 
    is_tenant_admin BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_users PRIMARY KEY (id), 
    CONSTRAINT fk_users_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email)
);

CREATE INDEX idx_users_tenant_id ON users (tenant_id);

CREATE TABLE roles (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_roles PRIMARY KEY (id), 
    CONSTRAINT fk_roles_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_roles_tenant_name UNIQUE (tenant_id, name)
);

CREATE TABLE user_roles (
    user_id UUID NOT NULL, 
    role_id UUID NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_user_roles PRIMARY KEY (user_id, role_id), 
    CONSTRAINT fk_user_roles_role_id_roles FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
    CONSTRAINT fk_user_roles_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE database_connections (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    created_by UUID, 
    name VARCHAR(200) NOT NULL, 
    database_type VARCHAR(50) NOT NULL, 
    host VARCHAR(255), 
    port INTEGER, 
    database_name VARCHAR(255), 
    username VARCHAR(255), 
    encrypted_password TEXT, 
    encrypted_connection_string TEXT, 
    ssl_enabled BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    ssl_settings JSONB DEFAULT '{}' NOT NULL, 
    connection_options JSONB DEFAULT '{}' NOT NULL, 
    status VARCHAR(30) DEFAULT 'pending' NOT NULL, 
    last_tested_at TIMESTAMP WITH TIME ZONE, 
    last_test_message TEXT, 
    schema_sync_status VARCHAR(30) DEFAULT 'pending', 
    last_schema_sync_at TIMESTAMP WITH TIME ZONE, 
    is_active BOOLEAN DEFAULT 'TRUE' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_database_connections PRIMARY KEY (id), 
    CONSTRAINT fk_database_connections_created_by_users FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL, 
    CONSTRAINT fk_database_connections_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_database_connection_name UNIQUE (tenant_id, name)
);

CREATE INDEX idx_database_connections_tenant ON database_connections (tenant_id);

CREATE TABLE database_schemas (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    connection_id UUID NOT NULL, 
    schema_name VARCHAR(255) NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_database_schemas PRIMARY KEY (id), 
    CONSTRAINT fk_database_schemas_connection_id_database_connections FOREIGN KEY(connection_id) REFERENCES database_connections (id) ON DELETE CASCADE, 
    CONSTRAINT fk_database_schemas_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_database_schema UNIQUE (connection_id, schema_name)
);

CREATE TABLE database_tables (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    connection_id UUID NOT NULL, 
    schema_id UUID, 
    table_name VARCHAR(255) NOT NULL, 
    table_type VARCHAR(50) DEFAULT 'table' NOT NULL, 
    description TEXT, 
    estimated_row_count BIGINT, 
    primary_key_columns JSONB DEFAULT '[]' NOT NULL, 
    is_enabled BOOLEAN DEFAULT 'TRUE' NOT NULL, 
    is_sensitive BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    metadata JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_database_tables PRIMARY KEY (id), 
    CONSTRAINT fk_database_tables_connection_id_database_connections FOREIGN KEY(connection_id) REFERENCES database_connections (id) ON DELETE CASCADE, 
    CONSTRAINT fk_database_tables_schema_id_database_schemas FOREIGN KEY(schema_id) REFERENCES database_schemas (id) ON DELETE CASCADE, 
    CONSTRAINT fk_database_tables_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_database_table UNIQUE (connection_id, schema_id, table_name)
);

CREATE TABLE database_columns (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    table_id UUID NOT NULL, 
    column_name VARCHAR(255) NOT NULL, 
    data_type VARCHAR(100) NOT NULL, 
    ordinal_position INTEGER, 
    is_nullable BOOLEAN, 
    is_primary_key BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    is_foreign_key BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    is_sensitive BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    referenced_schema VARCHAR(255), 
    referenced_table VARCHAR(255), 
    referenced_column VARCHAR(255), 
    description TEXT, 
    sample_values JSONB DEFAULT '[]' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_database_columns PRIMARY KEY (id), 
    CONSTRAINT fk_database_columns_table_id_database_tables FOREIGN KEY(table_id) REFERENCES database_tables (id) ON DELETE CASCADE, 
    CONSTRAINT fk_database_columns_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_database_column UNIQUE (table_id, column_name)
);

CREATE TABLE table_permissions (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    role_id UUID, 
    user_id UUID, 
    connection_id UUID NOT NULL, 
    table_id UUID NOT NULL, 
    can_read BOOLEAN DEFAULT 'TRUE' NOT NULL, 
    can_insert BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    can_update BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    can_delete BOOLEAN DEFAULT 'FALSE' NOT NULL, 
    row_filter JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_table_permissions PRIMARY KEY (id), 
    CONSTRAINT chk_table_permissions_chk_permission_subject CHECK ((role_id IS NOT NULL AND user_id IS NULL) OR (role_id IS NULL AND user_id IS NOT NULL)), 
    CONSTRAINT fk_table_permissions_connection_id_database_connections FOREIGN KEY(connection_id) REFERENCES database_connections (id) ON DELETE CASCADE, 
    CONSTRAINT fk_table_permissions_role_id_roles FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
    CONSTRAINT fk_table_permissions_table_id_database_tables FOREIGN KEY(table_id) REFERENCES database_tables (id) ON DELETE CASCADE, 
    CONSTRAINT fk_table_permissions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT fk_table_permissions_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE column_permissions (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    table_permission_id UUID NOT NULL, 
    column_id UUID NOT NULL, 
    can_read BOOLEAN DEFAULT 'TRUE' NOT NULL, 
    can_filter BOOLEAN DEFAULT 'TRUE' NOT NULL, 
    can_aggregate BOOLEAN DEFAULT 'TRUE' NOT NULL, 
    mask_type VARCHAR(50), 
    CONSTRAINT pk_column_permissions PRIMARY KEY (id), 
    CONSTRAINT fk_column_permissions_column_id_database_columns FOREIGN KEY(column_id) REFERENCES database_columns (id) ON DELETE CASCADE, 
    CONSTRAINT fk_column_permissions_table_permission_id_table_permissions FOREIGN KEY(table_permission_id) REFERENCES table_permissions (id) ON DELETE CASCADE, 
    CONSTRAINT uq_column_permission UNIQUE (table_permission_id, column_id)
);

CREATE TABLE knowledge_bases (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    created_by UUID, 
    name VARCHAR(200) NOT NULL, 
    description TEXT, 
    embedding_model VARCHAR(255), 
    chunking_config JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_knowledge_bases PRIMARY KEY (id), 
    CONSTRAINT fk_knowledge_bases_created_by_users FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE SET NULL, 
    CONSTRAINT fk_knowledge_bases_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_knowledge_base_name UNIQUE (tenant_id, name)
);

CREATE TABLE files (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    knowledge_base_id UUID, 
    uploaded_by UUID, 
    original_name VARCHAR(500) NOT NULL, 
    stored_name VARCHAR(500) NOT NULL, 
    storage_path TEXT NOT NULL, 
    mime_type VARCHAR(255), 
    extension VARCHAR(30), 
    file_size_bytes BIGINT, 
    checksum VARCHAR(128), 
    processing_status VARCHAR(30) DEFAULT 'pending' NOT NULL, 
    processing_error TEXT, 
    page_count INTEGER, 
    extracted_text_length BIGINT, 
    metadata JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    processed_at TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT pk_files PRIMARY KEY (id), 
    CONSTRAINT fk_files_knowledge_base_id_knowledge_bases FOREIGN KEY(knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE SET NULL, 
    CONSTRAINT fk_files_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT fk_files_uploaded_by_users FOREIGN KEY(uploaded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE TABLE document_chunks (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    knowledge_base_id UUID NOT NULL, 
    file_id UUID NOT NULL, 
    chunk_index INTEGER NOT NULL, 
    content TEXT NOT NULL, 
    content_hash VARCHAR(128), 
    page_number INTEGER, 
    section_title TEXT, 
    token_count INTEGER, 
    metadata JSONB DEFAULT '{}' NOT NULL, 
    embedding VECTOR(1024), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_document_chunks PRIMARY KEY (id), 
    CONSTRAINT fk_document_chunks_file_id_files FOREIGN KEY(file_id) REFERENCES files (id) ON DELETE CASCADE, 
    CONSTRAINT fk_document_chunks_knowledge_base_id_knowledge_bases FOREIGN KEY(knowledge_base_id) REFERENCES knowledge_bases (id) ON DELETE CASCADE, 
    CONSTRAINT fk_document_chunks_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT uq_document_chunk UNIQUE (file_id, chunk_index)
);

CREATE TABLE conversations (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    title VARCHAR(500), 
    status VARCHAR(30) DEFAULT 'active' NOT NULL, 
    active_connection_ids JSONB DEFAULT '[]' NOT NULL, 
    active_knowledge_base_ids JSONB DEFAULT '[]' NOT NULL, 
    settings JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    last_message_at TIMESTAMP WITH TIME ZONE, 
    CONSTRAINT pk_conversations PRIMARY KEY (id), 
    CONSTRAINT fk_conversations_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
    CONSTRAINT fk_conversations_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE messages (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    conversation_id UUID NOT NULL, 
    parent_message_id UUID, 
    role VARCHAR(30) NOT NULL, 
    message_type VARCHAR(30) DEFAULT 'text' NOT NULL, 
    content TEXT NOT NULL, 
    structured_content JSONB, 
    detected_intent VARCHAR(50), 
    selected_sources JSONB DEFAULT '[]' NOT NULL, 
    model_name VARCHAR(255), 
    prompt_tokens INTEGER, 
    completion_tokens INTEGER, 
    latency_ms INTEGER, 
    status VARCHAR(30) DEFAULT 'completed' NOT NULL, 
    error_message TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_messages PRIMARY KEY (id), 
    CONSTRAINT fk_messages_conversation_id_conversations FOREIGN KEY(conversation_id) REFERENCES conversations (id) ON DELETE CASCADE, 
    CONSTRAINT fk_messages_parent_message_id_messages FOREIGN KEY(parent_message_id) REFERENCES messages (id) ON DELETE SET NULL, 
    CONSTRAINT fk_messages_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE TABLE query_executions (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    conversation_id UUID, 
    message_id UUID, 
    connection_id UUID NOT NULL, 
    generated_sql TEXT NOT NULL, 
    normalized_sql TEXT, 
    query_type VARCHAR(30), 
    validation_status VARCHAR(30) NOT NULL, 
    validation_errors JSONB DEFAULT '[]' NOT NULL, 
    applied_row_filters JSONB DEFAULT '{}' NOT NULL, 
    referenced_tables JSONB DEFAULT '[]' NOT NULL, 
    referenced_columns JSONB DEFAULT '[]' NOT NULL, 
    execution_status VARCHAR(30), 
    execution_time_ms INTEGER, 
    returned_row_count INTEGER, 
    result_preview JSONB, 
    error_code VARCHAR(100), 
    error_message TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_query_executions PRIMARY KEY (id), 
    CONSTRAINT fk_query_executions_connection_id_database_connections FOREIGN KEY(connection_id) REFERENCES database_connections (id) ON DELETE CASCADE, 
    CONSTRAINT fk_query_executions_conversation_id_conversations FOREIGN KEY(conversation_id) REFERENCES conversations (id) ON DELETE SET NULL, 
    CONSTRAINT fk_query_executions_message_id_messages FOREIGN KEY(message_id) REFERENCES messages (id) ON DELETE SET NULL, 
    CONSTRAINT fk_query_executions_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE TABLE message_citations (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID NOT NULL, 
    message_id UUID NOT NULL, 
    citation_type VARCHAR(30) NOT NULL, 
    file_id UUID, 
    chunk_id UUID, 
    query_execution_id UUID, 
    title TEXT, 
    source_reference TEXT, 
    page_number INTEGER, 
    relevance_score NUMERIC(8, 6), 
    metadata JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_message_citations PRIMARY KEY (id), 
    CONSTRAINT fk_message_citations_chunk_id_document_chunks FOREIGN KEY(chunk_id) REFERENCES document_chunks (id) ON DELETE SET NULL, 
    CONSTRAINT fk_message_citations_file_id_files FOREIGN KEY(file_id) REFERENCES files (id) ON DELETE SET NULL, 
    CONSTRAINT fk_message_citations_message_id_messages FOREIGN KEY(message_id) REFERENCES messages (id) ON DELETE CASCADE, 
    CONSTRAINT fk_message_citations_query_execution_id_query_executions FOREIGN KEY(query_execution_id) REFERENCES query_executions (id) ON DELETE SET NULL, 
    CONSTRAINT fk_message_citations_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE TABLE audit_logs (
    id UUID DEFAULT uuid_generate_v4() NOT NULL, 
    tenant_id UUID, 
    user_id UUID, 
    action VARCHAR(100) NOT NULL, 
    resource_type VARCHAR(100), 
    resource_id UUID, 
    ip_address INET, 
    user_agent TEXT, 
    request_id VARCHAR(100), 
    details JSONB DEFAULT '{}' NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    CONSTRAINT pk_audit_logs PRIMARY KEY (id), 
    CONSTRAINT fk_audit_logs_tenant_id_tenants FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE SET NULL, 
    CONSTRAINT fk_audit_logs_user_id_users FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
);

INSERT INTO alembic_version (version_num) VALUES ('0001_initial_schema') RETURNING alembic_version.version_num;

-- Running upgrade 0001_initial_schema -> 0002_permission_extensions

CREATE UNIQUE INDEX idx_table_permissions_user_grant ON table_permissions (user_id, connection_id, table_id) WHERE user_id IS NOT NULL;

CREATE UNIQUE INDEX idx_table_permissions_role_grant ON table_permissions (role_id, connection_id, table_id) WHERE role_id IS NOT NULL;

UPDATE alembic_version SET version_num='0002_permission_extensions' WHERE alembic_version.version_num = '0001_initial_schema';

COMMIT;

