from typing import Optional
import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKeyConstraint, Index, Integer, LargeBinary, PrimaryKeyConstraint, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from db.clsEncryptedBytes import clsEncryptedBytes

class Base(DeclarativeBase):
    pass


class TApplicationApp(Base):
    __tablename__ = 't_application_app'
    __table_args__ = (
        PrimaryKeyConstraint('app_id', name='pk_app'),
        UniqueConstraint('app_code', name='uq_app_code'),
        {'schema': 'ihm'}
    )

    app_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    app_code: Mapped[str] = mapped_column(String(32), nullable=False)
    app_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    app_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    app_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    app_description: Mapped[Optional[str]] = mapped_column(String(512))

    t_app_lan_nal: Mapped[list['TAppLanNal']] = relationship('TAppLanNal', back_populates='app')
    t_element_ele: Mapped[list['TElementEle']] = relationship('TElementEle', back_populates='app')


class TLangueLan(Base):
    __tablename__ = 't_langue_lan'
    __table_args__ = (
        PrimaryKeyConstraint('lan_id', name='pk_lan'),
        UniqueConstraint('lan_code', name='uq_lan_code'),
        {'schema': 'ihm'}
    )

    lan_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lan_code: Mapped[str] = mapped_column(String(32), nullable=False)
    lan_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    lan_rtl: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    lan_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    lan_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lan_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lan_ordre: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    t_app_lan_nal: Mapped[list['TAppLanNal']] = relationship('TAppLanNal', back_populates='lan')
    t_libelle_element_lel: Mapped[list['TLibelleElementLel']] = relationship('TLibelleElementLel', back_populates='lan')
    t_libelle_relation_lre: Mapped[list['TLibelleRelationLre']] = relationship('TLibelleRelationLre', back_populates='lan')
    t_libelle_colonne_lco: Mapped[list['TLibelleColonneLco']] = relationship('TLibelleColonneLco', back_populates='lan')


class TTypeAffichageTaf(Base):
    __tablename__ = 't_type_affichage_taf'
    __table_args__ = (
        PrimaryKeyConstraint('taf_id', name='pk_taf'),
        UniqueConstraint('taf_code', name='uq_taf_code'),
        {'schema': 'ihm'}
    )

    taf_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    taf_code: Mapped[str] = mapped_column(String(32), nullable=False)
    taf_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    taf_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    taf_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)

    t_colonne_col: Mapped[list['TColonneCol']] = relationship('TColonneCol', back_populates='taf')


class TTypeElementTel(Base):
    __tablename__ = 't_type_element_tel'
    __table_args__ = (
        PrimaryKeyConstraint('tel_id', name='pk_tel'),
        UniqueConstraint('tel_code', name='uq_tel_code'),
        {'schema': 'ihm'}
    )

    tel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tel_code: Mapped[str] = mapped_column(String(32), nullable=False)
    tel_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    tel_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    tel_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)

    t_element_ele: Mapped[list['TElementEle']] = relationship('TElementEle', back_populates='tel')


class TTypeRelationTre(Base):
    __tablename__ = 't_type_relation_tre'
    __table_args__ = (
        PrimaryKeyConstraint('tre_id', name='pk_tre'),
        UniqueConstraint('tre_code', name='uq_tre_code'),
        {'schema': 'ihm'}
    )

    tre_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tre_code: Mapped[str] = mapped_column(String(32), nullable=False)
    tre_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    tre_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    tre_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)

    t_relation_rel: Mapped[list['TRelationRel']] = relationship('TRelationRel', back_populates='tre')


class TBaseBas(Base):
    __tablename__ = 't_base_bas'
    __table_args__ = (
        PrimaryKeyConstraint('bas_id', name='t_base_bas_pkey'),
        UniqueConstraint('bas_nom', name='t_base_bas_bas_nom_key'),
        Index('ix_bas_bas_nom', 'bas_nom', unique=True),
        {'schema': 'public'}
    )

    bas_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bas_nom: Mapped[str] = mapped_column(String(20), nullable=False)
    bas_description: Mapped[Optional[str]] = mapped_column(String(75))

    t_bas_env_nbe: Mapped[list['TBasEnvNbe']] = relationship('TBasEnvNbe', back_populates='bas')


class TEnvironnementEnv(Base):
    __tablename__ = 't_environnement_env'
    __table_args__ = (
        PrimaryKeyConstraint('env_id', name='t_environnement_env_pkey'),
        UniqueConstraint('env_code', name='t_environnement_env_env_code_key'),
        Index('ix_env_env_code', 'env_code', unique=True),
        {'schema': 'public'}
    )

    env_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    env_code: Mapped[str] = mapped_column(String(10), nullable=False)
    env_description: Mapped[Optional[str]] = mapped_column(String(50))

    t_bas_env_nbe: Mapped[list['TBasEnvNbe']] = relationship('TBasEnvNbe', back_populates='env')


class TBaseBas_(Base):
    __tablename__ = 't_base_bas'
    __table_args__ = (
        PrimaryKeyConstraint('bas_id', name='t_base_bas_pkey'),
        UniqueConstraint('bas_nom', name='t_base_bas_bas_nom_key'),
        Index('ix_bas_bas_nom', 'bas_nom', unique=True)
    )

    bas_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bas_nom: Mapped[str] = mapped_column(String(20), nullable=False)
    bas_description: Mapped[Optional[str]] = mapped_column(String(75))

    t_db_db: Mapped[list['TDbDb']] = relationship('TDbDb', back_populates='bas')


class TEnvironnementEnv_(Base):
    __tablename__ = 't_environnement_env'
    __table_args__ = (
        PrimaryKeyConstraint('env_id', name='t_environnement_env_pkey'),
        UniqueConstraint('env_code', name='t_environnement_env_env_code_key'),
        Index('ix_env_env_code', 'env_code', unique=True)
    )

    env_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    env_code: Mapped[str] = mapped_column(String(10), nullable=False)
    env_description: Mapped[Optional[str]] = mapped_column(String(50))

    t_db_db: Mapped[list['TDbDb']] = relationship('TDbDb', back_populates='env')


class TAppLanNal(Base):
    __tablename__ = 't_app_lan_nal'
    __table_args__ = (
        ForeignKeyConstraint(['app_id'], ['ihm.t_application_app.app_id'], name='fk_nal_app'),
        ForeignKeyConstraint(['lan_id'], ['ihm.t_langue_lan.lan_id'], name='fk_nal_lan'),
        PrimaryKeyConstraint('app_id', 'lan_id', name='pk_nal'),
        {'schema': 'ihm'}
    )

    app_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lan_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nal_est_defaut: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    nal_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    nal_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)

    app: Mapped['TApplicationApp'] = relationship('TApplicationApp', back_populates='t_app_lan_nal')
    lan: Mapped['TLangueLan'] = relationship('TLangueLan', back_populates='t_app_lan_nal')


class TDbDb(Base):
    __tablename__ = 't_db_db'
    __table_args__ = (
        ForeignKeyConstraint(['bas_id'], ['t_base_bas.bas_id'], ondelete='SET NULL', name='fk_db_bas'),
        ForeignKeyConstraint(['env_id'], ['t_environnement_env.env_id'], ondelete='SET NULL', name='fk_db_env'),
        PrimaryKeyConstraint('db_id', name='pk_db'),
        UniqueConstraint('db_code', name='uq_db_code'),
        {'schema': 'ihm'}
    )

    db_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    db_code: Mapped[str] = mapped_column(String(32), nullable=False)
    db_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    db_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    db_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    db_description: Mapped[Optional[str]] = mapped_column(String(512))
    env_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    bas_id: Mapped[Optional[int]] = mapped_column(BigInteger)

    bas: Mapped[Optional['TBaseBas_']] = relationship('TBaseBas_', back_populates='t_db_db')
    env: Mapped[Optional['TEnvironnementEnv_']] = relationship('TEnvironnementEnv_', back_populates='t_db_db')
    t_db_rapport_dbr: Mapped[list['TDbRapportDbr']] = relationship('TDbRapportDbr', back_populates='db')
    t_schema_sch: Mapped[list['TSchemaSch']] = relationship('TSchemaSch', back_populates='db')


class TElementEle(Base):
    __tablename__ = 't_element_ele'
    __table_args__ = (
        ForeignKeyConstraint(['app_id'], ['ihm.t_application_app.app_id'], name='fk_ele_app'),
        ForeignKeyConstraint(['tel_id'], ['ihm.t_type_element_tel.tel_id'], name='fk_ele_tel'),
        PrimaryKeyConstraint('ele_id', name='pk_ele'),
        UniqueConstraint('app_id', 'ele_cle', name='uq_ele'),
        {'schema': 'ihm'}
    )

    ele_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    app_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ele_cle: Mapped[str] = mapped_column(String(32), nullable=False)
    ele_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    ele_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    ele_description: Mapped[Optional[str]] = mapped_column(String(256))

    app: Mapped['TApplicationApp'] = relationship('TApplicationApp', back_populates='t_element_ele')
    tel: Mapped['TTypeElementTel'] = relationship('TTypeElementTel', back_populates='t_element_ele')
    t_libelle_element_lel: Mapped[list['TLibelleElementLel']] = relationship('TLibelleElementLel', back_populates='ele')


class TBasEnvNbe(Base):
    __tablename__ = 't_bas_env_nbe'
    __table_args__ = (
        ForeignKeyConstraint(['bas_id'], ['public.t_base_bas.bas_id'], name='t_bas_env_nbe_bas_id_fkey'),
        ForeignKeyConstraint(['env_id'], ['public.t_environnement_env.env_id'], name='t_bas_env_nbe_env_id_fkey'),
        PrimaryKeyConstraint('bas_id', 'env_id', name='t_bas_env_nbe_pkey'),
        UniqueConstraint('bas_id', 'env_id', name='t_bas_env_nbe_bas_id_env_id_key'),
        Index('ix_nbe_bas_id_env_id', 'bas_id', 'env_id', postgresql_with={'fillfactor': '100', 'deduplicate_items': 'true'}, unique=True),
        {'schema': 'public'}
    )

    bas_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    env_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nbe_db_name: Mapped[str] = mapped_column(String(100), nullable=False)
    nbe_host: Mapped[Optional[bytes]] = mapped_column(clsEncryptedBytes, comment='encrypted')
    nbe_port: Mapped[Optional[int]] = mapped_column(Integer, server_default=text('5432'))
    nbe_user: Mapped[Optional[bytes]] = mapped_column(clsEncryptedBytes, comment='encrypted')
    nbe_pwd: Mapped[Optional[bytes]] = mapped_column(clsEncryptedBytes, comment='encrypted')
    nbe_ssh_enabled: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))
    nbe_ssh_host: Mapped[Optional[bytes]] = mapped_column(clsEncryptedBytes, comment='encrypted')
    nbe_ssh_user: Mapped[Optional[bytes]] = mapped_column(clsEncryptedBytes, comment='encrypted')
    nbe_ssh_key_path: Mapped[Optional[bytes]] = mapped_column(clsEncryptedBytes, comment='encrypted')
    nbe_ssh_port: Mapped[Optional[int]] = mapped_column(Integer)

    bas: Mapped['TBaseBas'] = relationship('TBaseBas', back_populates='t_bas_env_nbe')
    env: Mapped['TEnvironnementEnv'] = relationship('TEnvironnementEnv', back_populates='t_bas_env_nbe')


class TDbRapportDbr(Base):
    __tablename__ = 't_db_rapport_dbr'
    __table_args__ = (
        ForeignKeyConstraint(['db_id'], ['ihm.t_db_db.db_id'], ondelete='CASCADE', name='fk_dbr_db'),
        PrimaryKeyConstraint('dbr_id', name='pk_dbr'),
        {'schema': 'ihm'}
    )

    dbr_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    db_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    dbr_date: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    dbr_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dbr_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    dbr_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)

    db: Mapped['TDbDb'] = relationship('TDbDb', back_populates='t_db_rapport_dbr')


class TLibelleElementLel(Base):
    __tablename__ = 't_libelle_element_lel'
    __table_args__ = (
        ForeignKeyConstraint(['ele_id'], ['ihm.t_element_ele.ele_id'], ondelete='CASCADE', name='fk_lel_ele'),
        ForeignKeyConstraint(['lan_id'], ['ihm.t_langue_lan.lan_id'], name='fk_lel_lan'),
        PrimaryKeyConstraint('ele_id', 'lan_id', name='pk_lel'),
        {'schema': 'ihm'}
    )

    ele_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lan_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lel_label: Mapped[str] = mapped_column(String(128), nullable=False)
    lel_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lel_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lel_tooltip: Mapped[Optional[str]] = mapped_column(String(512))

    ele: Mapped['TElementEle'] = relationship('TElementEle', back_populates='t_libelle_element_lel')
    lan: Mapped['TLangueLan'] = relationship('TLangueLan', back_populates='t_libelle_element_lel')


class TSchemaSch(Base):
    __tablename__ = 't_schema_sch'
    __table_args__ = (
        ForeignKeyConstraint(['db_id'], ['ihm.t_db_db.db_id'], name='fk_sch_db'),
        PrimaryKeyConstraint('sch_id', name='pk_sch'),
        UniqueConstraint('db_id', 'sch_nom', name='uq_sch'),
        {'schema': 'ihm'}
    )

    sch_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    db_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sch_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    sch_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    sch_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    sch_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))

    db: Mapped['TDbDb'] = relationship('TDbDb', back_populates='t_schema_sch')
    t_relation_rel: Mapped[list['TRelationRel']] = relationship('TRelationRel', back_populates='sch')


class TRelationRel(Base):
    __tablename__ = 't_relation_rel'
    __table_args__ = (
        ForeignKeyConstraint(['sch_id'], ['ihm.t_schema_sch.sch_id'], ondelete='CASCADE', name='fk_rel_sch'),
        ForeignKeyConstraint(['tre_id'], ['ihm.t_type_relation_tre.tre_id'], name='fk_rel_tre'),
        PrimaryKeyConstraint('rel_id', name='pk_rel'),
        UniqueConstraint('sch_id', 'rel_nom', name='uq_rel'),
        {'schema': 'ihm'}
    )

    rel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sch_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    tre_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rel_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    rel_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    rel_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    rel_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))

    sch: Mapped['TSchemaSch'] = relationship('TSchemaSch', back_populates='t_relation_rel')
    tre: Mapped['TTypeRelationTre'] = relationship('TTypeRelationTre', back_populates='t_relation_rel')
    t_colonne_col: Mapped[list['TColonneCol']] = relationship('TColonneCol', back_populates='rel')
    t_libelle_relation_lre: Mapped[list['TLibelleRelationLre']] = relationship('TLibelleRelationLre', back_populates='rel')


class TColonneCol(Base):
    __tablename__ = 't_colonne_col'
    __table_args__ = (
        ForeignKeyConstraint(['rel_id'], ['ihm.t_relation_rel.rel_id'], ondelete='CASCADE', name='fk_col_rel'),
        ForeignKeyConstraint(['taf_id'], ['ihm.t_type_affichage_taf.taf_id'], name='fk_col_taf'),
        PrimaryKeyConstraint('col_id', name='pk_col'),
        UniqueConstraint('rel_id', 'col_nom', name='uq_col'),
        Index('uq_col_rel_nom', 'rel_id', 'col_nom', unique=True),
        {'schema': 'ihm'}
    )

    col_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    rel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    taf_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    col_nom: Mapped[str] = mapped_column(String(128), nullable=False)
    col_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    col_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    col_actif: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    col_largeur: Mapped[Optional[int]] = mapped_column(Integer)

    rel: Mapped['TRelationRel'] = relationship('TRelationRel', back_populates='t_colonne_col')
    taf: Mapped['TTypeAffichageTaf'] = relationship('TTypeAffichageTaf', back_populates='t_colonne_col')
    t_libelle_colonne_lco: Mapped[list['TLibelleColonneLco']] = relationship('TLibelleColonneLco', back_populates='col')


class TLibelleRelationLre(Base):
    __tablename__ = 't_libelle_relation_lre'
    __table_args__ = (
        ForeignKeyConstraint(['lan_id'], ['ihm.t_langue_lan.lan_id'], name='fk_lre_lan'),
        ForeignKeyConstraint(['rel_id'], ['ihm.t_relation_rel.rel_id'], ondelete='CASCADE', name='fk_lre_rel'),
        PrimaryKeyConstraint('rel_id', 'lan_id', name='pk_lre'),
        {'schema': 'ihm'}
    )

    rel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lan_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lre_label: Mapped[str] = mapped_column(String(128), nullable=False)
    lre_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lre_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lre_tooltip: Mapped[Optional[str]] = mapped_column(String(512))

    lan: Mapped['TLangueLan'] = relationship('TLangueLan', back_populates='t_libelle_relation_lre')
    rel: Mapped['TRelationRel'] = relationship('TRelationRel', back_populates='t_libelle_relation_lre')


class TLibelleColonneLco(Base):
    __tablename__ = 't_libelle_colonne_lco'
    __table_args__ = (
        ForeignKeyConstraint(['col_id'], ['ihm.t_colonne_col.col_id'], ondelete='CASCADE', name='fk_lco_col'),
        ForeignKeyConstraint(['lan_id'], ['ihm.t_langue_lan.lan_id'], name='fk_lco_lan'),
        PrimaryKeyConstraint('col_id', 'lan_id', name='pk_lco'),
        {'schema': 'ihm'}
    )

    col_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lan_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    lco_label: Mapped[str] = mapped_column(String(128), nullable=False)
    lco_cree_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lco_modifie_le: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False)
    lco_tooltip: Mapped[Optional[str]] = mapped_column(String(512))
    lco_label_court: Mapped[Optional[str]] = mapped_column(String(15))

    col: Mapped['TColonneCol'] = relationship('TColonneCol', back_populates='t_libelle_colonne_lco')
    lan: Mapped['TLangueLan'] = relationship('TLangueLan', back_populates='t_libelle_colonne_lco')
